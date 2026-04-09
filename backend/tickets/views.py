from http import cookies
import traceback
from .models import TicketPredictionLog
from rest_framework import viewsets
from .models import Ticket, TicketComment,TicketPredictionLog
from .serializers import TicketCommentSerializer

from requests import request
from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticated
from rest_framework.exceptions import PermissionDenied
from django.http import JsonResponse                         
from django.db.models import Q, Count
from rest_framework.decorators import api_view, authentication_classes, permission_classes
from rest_framework.response import Response
from rest_framework.views import APIView

from .tasks import send_email_task
from .models import Ticket
from users.models import AgentProfile
from .models import Ticket, Category, TicketPredictionLog
from .serializers import TicketSerializer, CategorySerializer
from users.permissions import IsAdmin
from users.pagination import CustomPagination
from .ai import predict_ticket
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.filters import SearchFilter

# CATEGORY
class test_backend(APIView):
    def get(self, request):
        return Response({"message": "Backend is working!"})

class CategoryViewSet(viewsets.ModelViewSet):
    queryset = Category.objects.all()
    serializer_class = CategorySerializer
    permission_classes = [IsAuthenticated, IsAdmin]
    pagination_class = None


# TICKETS

class TicketViewSet(viewsets.ModelViewSet):
    serializer_class = TicketSerializer
    permission_classes = [IsAuthenticated]
    pagination_class = CustomPagination
    filter_backends = [DjangoFilterBackend, SearchFilter]
    filterset_fields = {
        'status': ['exact'],
        'priority': ['exact'],
        'category': ['exact'],
    }
    search_fields = ['title', 'description']

    def get_queryset(self):
        user = self.request.user
        print("AUTH USER:", user)
        print("AUTHENTICATED:", user.is_authenticated)
        print("ROLE:", getattr(user, "role", None))

        queryset = Ticket.objects.all()

        if not user.is_authenticated:
            print("NOT AUTHENTICATED")
            return Ticket.objects.none()

        role = str(user.role).lower().strip()
        print("NORMALIZED ROLE:", role)

        if role == "admin":
            assigned = self.request.query_params.get("assigned")
            if assigned == "true":
                queryset = queryset.filter(assigned_to__isnull=False)
            elif assigned == "false":
                queryset = queryset.filter(assigned_to__isnull=True)

            print("ADMIN COUNT:", queryset.count())
            return queryset

        if role == "agent":
            qs = queryset.filter(assigned_to=user)
            print("AGENT COUNT:", qs.count())
            return qs

        if role == "customer":
            qs = queryset.filter(customer=user)
            print("CUSTOMER COUNT:", qs.count())
            return qs

        print("FALLBACK NONE")
        return Ticket.objects.none()

    # CREATE
    def perform_create(self, serializer):
        if self.request.user.role.lower() != 'customer':
            raise PermissionDenied("Only customers can create tickets.")
        serializer.save(customer=self.request.user)


    # UPDATE
    def update(self, request, *args, **kwargs):
        ticket = self.get_object()
        user = request.user

        if user.role.lower() == 'customer':
            raise PermissionDenied("Customers cannot update tickets.")

        if user.role.lower() == 'agent' and ticket.assigned_to != user:
            raise PermissionDenied("You can only update your assigned tickets.")

        if user.role.lower() == 'agent':
            allowed_fields = {'status'}
            if not set(request.data.keys()).issubset(allowed_fields):
                raise PermissionDenied("Agents can only update ticket status.")

        # 🔥 Let serializer handle everything
        response = super().update(request, *args, **kwargs)
        print("DATA:", request.data)

        # refresh updated ticket
        ticket.refresh_from_db()

        update_prediction_feedback(ticket)
        # send email
        send_email_task.delay(
            ticket.customer.email,
            subject=f"Your ticket '{ticket.title}' updated",
            template_name="emails/ticket_status_updated.html",
            context={
                "customer_name": ticket.customer.username,
                "ticket_title": ticket.title,
                "new_status": ticket.status,
            }
        )

        return response
    
    

# STATS
@api_view(['GET'])
@permission_classes([IsAuthenticated])  
def ticket_stats(request):
    user = request.user
    try:
        if user.role.lower() == 'admin':
            queryset = Ticket.objects.all()
        elif user.role.lower() == 'agent':
            queryset = Ticket.objects.filter(assigned_to=user)
        else:
            queryset = Ticket.objects.filter(customer=user)

        stats = queryset.aggregate(
            total=Count('id'),
            open=Count('id', filter=Q(status='open')),
            in_progress=Count('id', filter=Q(status='in_progress')),
            closed=Count('id', filter=Q(status='closed')),
        )
        return Response(stats)
    except Exception as e:
        print(traceback.format_exc())
        return JsonResponse({"error": str(e)}, status=500)  

@api_view(['PATCH'])
@permission_classes([IsAuthenticated])
def assign_ticket(request, ticket_id):
    if request.user.role.lower() != 'admin':
        raise PermissionDenied("Only admins can assign tickets.")

    try:
        ticket = Ticket.objects.get(id=ticket_id)
    except Ticket.DoesNotExist:
        return Response({"error": "Ticket not found"}, status=404)

    agent_id = request.data.get("agent_id")
    print("agent_id received:", agent_id)
    print("ticket.category:", ticket.category)

    if agent_id:
        try:
            profile = AgentProfile.objects.select_related('user').get(user__id=agent_id)
        except AgentProfile.DoesNotExist:
            return Response({"error": f"No AgentProfile found for user id {agent_id}"}, status=404)

        ticket.assigned_to = profile.user
        ticket.status = "in_progress"
        ticket.save()
        return Response({"message": f"Ticket assigned to {profile.user.username}"})

    # Auto-assign
    category_name = ticket.category.name if hasattr(ticket.category, 'name') else ticket.category

    matching_profiles = (
        AgentProfile.objects
        .filter(is_available=True, categories__name__iexact=category_name)
        .select_related('user')
        .prefetch_related('categories')
        .distinct()
    )

    print("matching profiles count:", matching_profiles.count())

    if not matching_profiles.exists():
        return Response({"error": "No available agents for this category"}, status=404)

    best_agent = min(
        matching_profiles,
        key=lambda p: Ticket.objects.filter(
            assigned_to=p.user, status__in=["open", "in_progress"]
        ).count()
    )

    ticket.assigned_to = best_agent.user
    ticket.status = "in_progress"
    ticket.save()
    return Response({
        "message": f"Auto-assigned to {best_agent.user.username}",
        "agent": best_agent.user.username
    })



@api_view(["GET"])
@permission_classes([IsAuthenticated])
def prediction_stats(request):
    logs = TicketPredictionLog.objects.filter(actual_category__isnull=False)

    total = logs.count()
    correct_category = logs.filter(category_correct=True).count()
    correct_priority = logs.filter(priority_correct=True).count()

    category_accuracy = round((correct_category / total) * 100, 2) if total else 0
    priority_accuracy = round((correct_priority / total) * 100, 2) if total else 0

    by_source = list(
        logs.values("source").annotate(count=Count("id")).order_by("-count")
    )

    review_needed = TicketPredictionLog.objects.filter(
        Q(confidence__lt=0.85) | Q(predicted_category="other")
    ).count()

    return Response({
        "total_evaluated": total,
        "category_accuracy": category_accuracy,
        "priority_accuracy": priority_accuracy,
        "by_source": by_source,
        "review_needed": review_needed,
    })

class TicketCommentViewSet(viewsets.ModelViewSet):
    serializer_class = TicketCommentSerializer
    permission_classes = [IsAuthenticated]
    http_method_names = ["get", "post", "delete"]

    def get_ticket(self):
        ticket_id = self.kwargs.get("ticket_id")
        try:
            return Ticket.objects.get(id=ticket_id)
        except Ticket.DoesNotExist:
            raise PermissionDenied("Ticket not found.")

    def get_queryset(self):
        user = self.request.user
        ticket = self.get_ticket()

        if user.role.lower() == "admin":
            queryset = TicketComment.objects.filter(ticket=ticket)

        elif user.role.lower() == "agent":
            if ticket.assigned_to != user:
                raise PermissionDenied("You can only view comments on your assigned tickets.")
            queryset = TicketComment.objects.filter(ticket=ticket)

        elif user.role.lower() == "customer":
            if ticket.customer != user:
                raise PermissionDenied("You can only view comments on your own tickets.")
            queryset = TicketComment.objects.filter(ticket=ticket, is_internal=False)

        else:
            raise PermissionDenied("Invalid role.")

        return queryset.select_related("user", "ticket")

    def perform_create(self, serializer):
        user = self.request.user
        ticket = self.get_ticket()
        comment = None

        if user.role.lower() == "admin":
            comment = serializer.save(ticket=ticket, user=user)

        elif user.role.lower() == "agent":
            if ticket.assigned_to != user:
                raise PermissionDenied("You can only comment on your assigned tickets.")
            comment = serializer.save(ticket=ticket, user=user)

        elif user.role.lower() == "customer":
            if ticket.customer != user:
                raise PermissionDenied("You can only comment on your own tickets.")
            comment = serializer.save(ticket=ticket, user=user, is_internal=False)

        else:
            raise PermissionDenied("Invalid role.")

        # send email only when admin/agent adds a PUBLIC comment
        if (
            comment
            and user.role.lower() in ["admin", "agent"]
            and not comment.is_internal
        ):
            send_email_task.delay(
                ticket.customer.email,
                subject=f"[Ticket #{ticket.id}] New comment on your ticket",
                template_name="emails/ticket_comment_added.html",
                context={
                    "customer_name": ticket.customer.username,
                    "ticket_title": ticket.title,
                    "ticket_id": ticket.id,
                    "comment_by": user.username,
                    "comment_message": comment.message[:300],
                    "comment_role": user.role.lower(),  # 🔥 important
                }
            )

    def destroy(self, request, *args, **kwargs):
        comment = self.get_object()
        user = request.user

        if user.role.lower() == "admin":
            return super().destroy(request, *args, **kwargs)

        if comment.user != user:
            raise PermissionDenied("You can only delete your own comments.")

        return super().destroy(request, *args, **kwargs)
    

def update_prediction_feedback(ticket):
    log = (
        TicketPredictionLog.objects
        .filter(ticket=ticket)
        .order_by("-created_at")
        .first()
    )

    if not log:
        return

    actual_category = ticket.category.name if ticket.category else None
    actual_priority = ticket.priority

    log.actual_category = actual_category
    log.actual_priority = actual_priority
    log.category_correct = (log.predicted_category == actual_category)
    log.priority_correct = (log.predicted_priority == actual_priority)
    log.save()
    
@api_view(["GET"])
@permission_classes([IsAuthenticated])
def ticket_prediction_feedback(request, ticket_id):
    try:
        ticket = Ticket.objects.get(id=ticket_id)
    except Ticket.DoesNotExist:
        return Response({"error": "Ticket not found"}, status=404)

    user = request.user
    role = user.role.lower()

    if role == "customer" and ticket.customer != user:
        raise PermissionDenied("You can only view your own tickets.")

    if role == "agent" and ticket.assigned_to != user:
        raise PermissionDenied("You can only view feedback for your assigned tickets.")

    log = (
        TicketPredictionLog.objects
        .filter(ticket=ticket)
        .order_by("-created_at")
        .first()
    )

    if not log:
        return Response({
            "ticket_id": ticket.id,
            "has_feedback": False,
            "message": "No prediction feedback found for this ticket."
        })

    return Response({
        "ticket_id": ticket.id,
        "has_feedback": True,
        "predicted_category": log.predicted_category,
        "actual_category": log.actual_category,
        "category_correct": log.category_correct,
        "predicted_priority": log.predicted_priority,
        "actual_priority": log.actual_priority,
        "priority_correct": log.priority_correct,
        "confidence": log.confidence,
        "source": log.source,
        "created_at": log.created_at,
    })