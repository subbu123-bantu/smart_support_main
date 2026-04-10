from django.db.models import Q
from rest_framework import viewsets
from rest_framework.decorators import api_view, permission_classes
from rest_framework.exceptions import PermissionDenied
from rest_framework.filters import SearchFilter
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from django_filters.rest_framework import DjangoFilterBackend

from tickets.models import Ticket, Category, TicketPredictionLog, TicketComment
from tickets.serializers import (
    TicketSerializer,
    CategorySerializer,
    TicketCommentSerializer,
)
from tickets.tasks import send_email_task
from users.permissions import IsAdmin
from users.pagination import CustomPagination

from .services.assignment import assign_ticket_to_agent, auto_assign_ticket
from .services.ticketcomments import (
    get_ticket_or_raise,
    get_comment_queryset_for_user,
    create_comment_for_user,
    can_delete_comment,
)
from .services.ticket_prediction_update import update_prediction_feedback, get_prediction_feedback
from .services.ticketstats import build_ticket_stats
from .services.ticket_prediction_feedback import ticket_prediction_feedback

class test_backend(APIView):
    def get(self, request):
        return Response({"message": "Backend is working!"})


class CategoryViewSet(viewsets.ModelViewSet):
    queryset = Category.objects.all()
    serializer_class = CategorySerializer
    permission_classes = [IsAuthenticated, IsAdmin]
    pagination_class = None


class TicketViewSet(viewsets.ModelViewSet):
    serializer_class = TicketSerializer
    permission_classes = [IsAuthenticated]
    pagination_class = CustomPagination
    filter_backends = [DjangoFilterBackend, SearchFilter]
    filterset_fields = {
        "status": ["exact"],
        "priority": ["exact"],
        "category": ["exact"],
    }
    search_fields = ["title", "description"]

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

        if role == "admin":
            assigned = self.request.query_params.get("assigned")
            if assigned == "true":
                queryset = queryset.filter(assigned_to__isnull=False)
            elif assigned == "false":
                queryset = queryset.filter(assigned_to__isnull=True)

            print("ADMIN COUNT:", queryset.count())
            return queryset

        if role == "agent":
            return queryset.filter(assigned_to=user)

        if role == "customer":
            return queryset.filter(customer=user)

        print("FALLBACK NONE")
        return Ticket.objects.none()

    def perform_create(self, serializer):
        if self.request.user.role.lower() != "customer":
            raise PermissionDenied("Only customers can create tickets.")
        serializer.save(customer=self.request.user)

    def update(self, request, *args, **kwargs):
        ticket = self.get_object()
        user = request.user

        if user.role.lower() == "customer":
            raise PermissionDenied("Customers cannot update tickets.")

        if user.role.lower() == "agent" and ticket.assigned_to != user:
            raise PermissionDenied("You can only update your assigned tickets.")

        if user.role.lower() == "agent":
            allowed_fields = {"status"}
            if not set(request.data.keys()).issubset(allowed_fields):
                raise PermissionDenied("Agents can only update ticket status.")

        # 🔥 Let serializer handle everything
        response = super().update(request, *args, **kwargs)

        ticket.refresh_from_db()
        update_prediction_feedback(ticket)

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

        return response
    
    

@api_view(["GET"])
@permission_classes([IsAuthenticated])
def ticket_stats(request):
    data, status_code = build_ticket_stats(request.user)
    return Response(data, status=status_code)


@api_view(["PATCH"])
@permission_classes([IsAuthenticated])
def assign_ticket(request, ticket_id):
    if request.user.role.lower() != "admin":
        raise PermissionDenied("Only admins can assign tickets.")

    try:
        ticket = Ticket.objects.get(id=ticket_id)
    except Ticket.DoesNotExist:
        return Response({"error": "Ticket not found"}, status=404)

    agent_id = request.data.get("agent_id")

    if agent_id:
        data, status_code = assign_ticket_to_agent(ticket, agent_id)
        return Response(data, status=status_code)

    data, status_code = auto_assign_ticket(ticket)
    return Response(data, status=status_code)


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
        logs.values("source").annotate(count=Q("id")).order_by("-count")
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
        return get_ticket_or_raise(ticket_id)

    def get_queryset(self):
        ticket = self.get_ticket()
        return get_comment_queryset_for_user(self.request.user, ticket)

    def perform_create(self, serializer):
        ticket = self.get_ticket()
        create_comment_for_user(serializer, self.request.user, ticket)

    def destroy(self, request, *args, **kwargs):
        comment = self.get_object()
        can_delete_comment(request.user, comment)
        return super().destroy(request, *args, **kwargs)


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def ticket_prediction_feedback(request, ticket_id):
    _, data, status_code = get_prediction_feedback(ticket_id, request.user)
    return Response(data, status=status_code)
