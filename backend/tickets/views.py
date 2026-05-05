import logging

from asgiref.sync import sync_to_async
from django.db.models import Q, Count
from django.views.decorators.http import require_GET, require_POST, require_http_methods
from django_filters.rest_framework import DjangoFilterBackend

from rest_framework import viewsets
from rest_framework.decorators import api_view, permission_classes, authentication_classes
from rest_framework.exceptions import PermissionDenied
from rest_framework.filters import SearchFilter
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.authentication import JWTAuthentication

from tickets.models import Ticket, Category, TicketPredictionLog
from tickets.serializers import TicketSerializer, CategorySerializer, TicketCommentSerializer
from tickets.tasks import send_email_task
from users.permissions import IsAdminOrReadOnly
from users.pagination import CustomPagination

from .ai.ai import predict_ticket_async
from .services.assignment import assign_ticket_to_agent, auto_assign_ticket
from .services.ticketcomments import (
    get_ticket_or_raise,
    get_comment_queryset_for_user,
    create_comment_for_user,
    can_delete_comment,
)
from .services.ticket_prediction_update import update_prediction_feedback, get_prediction_feedback
from .services.ticketstats import build_ticket_stats_async

logger = logging.getLogger(__name__)


def _build_prediction_stats_payload():
    logs = TicketPredictionLog.objects.exclude(actual_category="")

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

    return {
        "total_evaluated": total,
        "category_accuracy": category_accuracy,
        "priority_accuracy": priority_accuracy,
        "by_source": by_source,
        "review_needed": review_needed,
    }


class test_backend(APIView):
    permission_classes = [AllowAny]
    def get(self, request):
        return Response({"message": "Backend is working!"})


class CategoryViewSet(viewsets.ModelViewSet):
    queryset = Category.objects.all()
    serializer_class = CategorySerializer
    permission_classes = [IsAdminOrReadOnly]
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
        if not user.is_authenticated:
            return Ticket.objects.none()

        role = str(user.role).lower().strip()
        queryset = Ticket.objects.select_related("category", "assigned_to", "customer").all()

        match role: 
            case "admin":
                assigned = self.request.query_params.get("assigned")
                if assigned == "true":
                    queryset = queryset.filter(assigned_to__isnull=False)
                elif assigned == "false":
                    queryset = queryset.filter(assigned_to__isnull=True)
                return queryset

            case "agent":
                return queryset.filter(assigned_to=user)

            case "customer":
                return queryset.filter(customer=user)
            case _:
                return Ticket.objects.none()

    def perform_create(self, serializer):
        if self.request.user.role.lower() != "customer":
            raise PermissionDenied("Only customers can create tickets.")
        serializer.save()

    def destroy(self, request, *args, **kwargs):
        raise PermissionDenied("Ticket deletion is not allowed.")

    def update(self, request, *args, **kwargs):
        ticket = self.get_object()
        user = request.user
        previous_status = ticket.status
        role = user.role.lower()

        match role:
            case "customer":
                raise PermissionDenied("Customers cannot update tickets.")

            case "admin" | "agent":
                if role == "agent":
                    if ticket.assigned_to != user:
                        raise PermissionDenied("You can only update your assigned tickets.")
                    allowed_fields = {"status", "priority"}
                    if not set(request.data.keys()).issubset(allowed_fields):
                        raise PermissionDenied("Agents can only update ticket status and priority.")

            case _:
                raise PermissionDenied("Invalid role.")

        response = super().update(request, *args, **kwargs)
        ticket.refresh_from_db()
        update_prediction_feedback(ticket)

        if ticket.status != previous_status:
            try:
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
            except Exception:
                logger.exception(
                    "Failed to queue ticket update email for ticket_id=%s", ticket.id
                )

        return response

@require_POST
@api_view(["POST"])
@authentication_classes([JWTAuthentication])
@permission_classes([IsAuthenticated])
async def predict_view(request):
    text = request.data.get("text", "").strip()
    if not text:
        return Response({"detail": "Text is required"}, status=400)

    result = await predict_ticket_async(text)

    return Response({
        "predicted_category": result["category"],
        "predicted_priority": result["priority"],
        "category_confidence": result["confidence"],
        "source": result["source"],
        "needs_manual_review": result["needs_manual_review"],
    })


@require_GET
@api_view(["GET"])
@permission_classes([IsAuthenticated])
async def ticket_stats(request):
    data, status_code = await build_ticket_stats_async(request.user)
    return Response(data, status=status_code)


@require_http_methods(["PATCH"])
@api_view(["PATCH"])
@permission_classes([IsAuthenticated])
async def assign_ticket(request, ticket_id):
    if request.user.role.lower() != "admin":
        raise PermissionDenied("Only admins can assign tickets.")

    try:
        ticket = await sync_to_async(Ticket.objects.get)(id=ticket_id)
    except Ticket.DoesNotExist:
        return Response({"error": "Ticket not found"}, status=404)

    if "agent_id" in request.data:
        agent_id = request.data.get("agent_id")
        if agent_id in (None, ""):
            return Response({"error": "agent_id cannot be empty"}, status=400)
        data, status_code = await sync_to_async(assign_ticket_to_agent)(ticket, agent_id)
        return Response(data, status=status_code)

    data, status_code = await sync_to_async(auto_assign_ticket)(ticket)
    return Response(data, status=status_code)


@require_GET
@api_view(["GET"])
@permission_classes([IsAuthenticated])
async def prediction_stats(request):
    if request.user.role.lower() != "admin":
        raise PermissionDenied("Only admins can view prediction stats.")

    data = await sync_to_async(_build_prediction_stats_payload)()
    return Response(data)


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


@require_GET
@api_view(["GET"])
@permission_classes([IsAuthenticated])
async def ticket_prediction_feedback(request, ticket_id):
    _, data, status_code = await sync_to_async(get_prediction_feedback)(ticket_id, request.user)
    return Response(data, status=status_code)
