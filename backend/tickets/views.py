from datetime import timedelta, timezone
from http import cookies
import traceback

from requests import request
from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticated
from rest_framework.exceptions import PermissionDenied
from django.http import JsonResponse                         
from django.db.models import Q, Count, Avg, F, ExpressionWrapper, DurationField
from django.db.models.functions import TruncDate
from rest_framework.decorators import api_view, authentication_classes, permission_classes
from rest_framework.response import Response
from rest_framework.views import APIView

from .tasks import send_email_task

from rest_framework import status
from .models import Ticket
from users.models import AgentProfile
from users.models import User
from .models import Ticket, Category, TicketPredictionLog
from .serializers import TicketSerializer, CategorySerializer
from users.permissions import IsAdmin
from users.pagination import CustomPagination
from .ai import predict_ticket
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.filters import SearchFilter
from rest_framework.permissions import AllowAny  

class test_backend(APIView):
    permission_classes = [AllowAny] 

    def get(self, request):
        return Response({"message": "Backend working"})

class CategoryViewSet(viewsets.ModelViewSet):
    queryset = Category.objects.all()
    serializer_class = CategorySerializer
    permission_classes = [IsAuthenticated, IsAdmin]


# TICKETS

class TicketViewSet(viewsets.ModelViewSet):
    serializer_class = TicketSerializer
    permission_classes = [IsAuthenticated]
    pagination_class = CustomPagination
    filter_backends = [DjangoFilterBackend, SearchFilter]
    filterset_fields = ['status', 'priority']
    search_fields = ['title', 'description']

    def get_queryset(self):
        user = self.request.user
        queryset = Ticket.objects.all()

        if not user.is_authenticated:
            return Ticket.objects.none()

        if user.role.lower() == "admin":
            assigned = self.request.query_params.get('assigned')
            if assigned == 'true':
                queryset = queryset.filter(assigned_to__isnull=False)
            elif assigned == 'false':
                queryset = queryset.filter(assigned_to__isnull=True)
            return queryset

        if user.role.lower() == "agent":
            return queryset.filter(assigned_to=user)

        if user.role.lower() == "customer":
            return queryset.filter(customer=user)

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

        response = super().update(request, *args, **kwargs)
 
        ticket.refresh_from_db()  # get updated status from DB
 
        send_email_task.delay(
            ticket.customer.email,
            subject=f"Your ticket '{ticket.title}' status updated to {ticket.status}",
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
 
        # Basic counts
        stats = queryset.aggregate(
            total=Count('id'),
            open=Count('id', filter=Q(status='open')),
            in_progress=Count('id', filter=Q(status='in_progress')),
            closed=Count('id', filter=Q(status='closed')),
        )
 
        # Admin-only extended analytics
        if user.role.lower() == 'admin':
 
            # Category breakdown
            by_category = list(
                queryset
                .values('category__name')
                .annotate(count=Count('id'))
                .order_by('-count')
            )
 
            # Priority breakdown
            by_priority = list(
                queryset
                .values('priority')
                .annotate(count=Count('id'))
                .order_by('-count')
            )
 
            # Tickets over last 7 days
            seven_days_ago = timezone.now() - timedelta(days=7)
            by_date = list(
                queryset
                .filter(created_at__gte=seven_days_ago)
                .annotate(date=TruncDate('created_at'))
                .values('date')
                .annotate(count=Count('id'))
                .order_by('date')
            )
            # Convert date objects to strings for JSON
            for entry in by_date:
                entry['date'] = str(entry['date'])
 
            # Agent workload
            agent_profiles = AgentProfile.objects.select_related('user').all()
            agent_workload = []
 
            for profile in agent_profiles:
                agent_tickets = Ticket.objects.filter(assigned_to=profile.user)
 
                assigned = agent_tickets.count()
                in_progress = agent_tickets.filter(status='in_progress').count()
                solved = agent_tickets.filter(status='closed').count()
 
                # Average resolution time (created_at → updated_at for closed tickets)
                avg_resolution = agent_tickets.filter(status='closed').aggregate(
                    avg=Avg(
                        ExpressionWrapper(
                            F('updated_at') - F('created_at'),
                            output_field=DurationField()
                        )
                    )
                )['avg']
 
                # Convert timedelta to hours
                avg_hours = None
                if avg_resolution:
                    avg_hours = round(avg_resolution.total_seconds() / 3600, 1)
 
                agent_workload.append({
                    "agent": profile.user.username,
                    "assigned": assigned,
                    "in_progress": in_progress,
                    "solved": solved,
                    "avg_resolution_hours": avg_hours,
                })
 
            # Sort by most assigned
            agent_workload.sort(key=lambda x: x['assigned'], reverse=True)
 
            stats['by_category'] = by_category
            stats['by_priority'] = by_priority
            stats['by_date'] = by_date
            stats['agent_workload'] = agent_workload
 
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