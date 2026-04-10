from rest_framework.exceptions import PermissionDenied

from tickets.models import Ticket, TicketPredictionLog


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


def get_prediction_feedback(ticket_id, user):
    try:
        ticket = Ticket.objects.get(id=ticket_id)
    except Ticket.DoesNotExist:
        return None, {
            "error": "Ticket not found"
        }, 404

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
        return ticket, {
            "ticket_id": ticket.id,
            "has_feedback": False,
            "message": "No prediction feedback found for this ticket."
        }, 200

    return ticket, {
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
    }, 200