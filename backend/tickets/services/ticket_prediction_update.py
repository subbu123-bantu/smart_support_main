from rest_framework.exceptions import PermissionDenied

from tickets.models import Ticket, TicketPredictionLog


class TicketPredictionFeedbackService:
    def _latest_log(self, ticket):
        return (
            TicketPredictionLog.objects
            .filter(ticket=ticket)
            .order_by("-created_at")
            .first()
        )

    def update_prediction_feedback(self, ticket):
        log = self._latest_log(ticket)
        if not log:
            return

        actual_category = ticket.category.name if ticket.category else ""
        actual_priority = ticket.priority if ticket.priority else ""

        log.actual_category = actual_category
        log.actual_priority = actual_priority
        log.category_correct = None if not actual_category else (
            (log.predicted_category or "").strip().lower() == actual_category.strip().lower()
        )
        log.priority_correct = None if not actual_priority else (
            (log.predicted_priority or "").strip().lower() == actual_priority.strip().lower()
        )
        log.save(update_fields=[
            "actual_category",
            "actual_priority",
            "category_correct",
            "priority_correct",
        ])

    def get_prediction_feedback(self, ticket_id, user):
        try:
            ticket = Ticket.objects.get(id=ticket_id)
        except Ticket.DoesNotExist:
            return None, {"error": "Ticket not found"}, 404

        role = user.role.lower()
        match role :
            case "customer":
                if ticket.customer != user:
                    raise PermissionDenied("You can only view your own tickets.")
            case "agent":
                if ticket.assigned_to != user:
                    raise PermissionDenied("You can only view feedback for your assigned tickets.")

        log = self._latest_log(ticket)
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


PREDICTION_FEEDBACK_SERVICE = TicketPredictionFeedbackService()


def update_prediction_feedback(ticket):
    return PREDICTION_FEEDBACK_SERVICE.update_prediction_feedback(ticket)


def get_prediction_feedback(ticket_id, user):
    return PREDICTION_FEEDBACK_SERVICE.get_prediction_feedback(ticket_id, user)
