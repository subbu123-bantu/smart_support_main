from tickets.models import TicketPredictionLog
from tickets.views import Ticket
from rest_framework.response import Response 
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.exceptions import PermissionDenied

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