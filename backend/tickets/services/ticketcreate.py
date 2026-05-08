import logging

from asgiref.sync import async_to_sync
from django.db import transaction
from django.db.models import Max

from tickets.ai.ai import log_prediction, predict_ticket_without_ai
from tickets.models import Ticket, Category
from tickets.services.assignment import auto_assign_ticket
from tickets.tasks import run_ai_fallback_prediction_task, send_email_task

logger = logging.getLogger(__name__)


class TicketCreationService:
    def _build_prediction_text(self, validated_data):
        return f"{validated_data.get('title', '')} {validated_data.get('description', '')}".strip()

    def _next_user_ticket_id(self, user):
        return (
            Ticket.objects
            .filter(customer=user)
            .select_for_update()
            .aggregate(Max("user_ticket_id"))["user_ticket_id__max"]
        ) or 0

    def _queue_created_email(self, ticket, user, category_name, priority, assignment_result):
        try:
            send_email_task.delay(
                ticket.customer.email,
                subject=f"Ticket '{ticket.title}' created successfully",
                template_name="emails/ticket_created.html",
                context={
                    "customer_name": user.username,
                    "ticket_title": ticket.title,
                    "category": category_name,
                    "priority": priority,
                    "assigned_agent": assignment_result.get("agent"),
                    "assigned": assignment_result.get("assigned", False),
                },
            )
        except Exception:
            logger.exception(
                "Failed to queue ticket created email for ticket_id=%s",
                ticket.id,
            )

    def _queue_ai_fallback(self, ticket, text_for_prediction, prediction):
        if not prediction.get("needs_manual_review", False):
            return

        try:
            # The create response should stay fast and deterministic, so the
            # slower AI-enrichment path runs after the transaction commits.
            run_ai_fallback_prediction_task.delay(ticket.id, text_for_prediction)
        except Exception:
            logger.exception(
                "Failed to queue AI fallback prediction for ticket_id=%s",
                ticket.id,
            )

    def create_ticket(self, validated_data, user):
        text_for_prediction = self._build_prediction_text(validated_data)
        prediction = async_to_sync(predict_ticket_without_ai)(text_for_prediction)

        category_name = prediction["category"].lower().strip()
        priority = prediction["priority"].lower()
        category_obj, _ = Category.objects.get_or_create(name=category_name)

        with transaction.atomic():
            ticket = Ticket.objects.create(
                **validated_data,
                customer=user,
                category=category_obj,
                priority=priority,
                predicted_category=category_name,
                predicted_priority=priority,
                user_ticket_id=self._next_user_ticket_id(user) + 1,
            )

            log_prediction(text_for_prediction, prediction, ticket)

            try:
                assignment_result, _ = auto_assign_ticket(ticket)
            except Exception:
                assignment_result = {"assigned": False, "agent": None}

            transaction.on_commit(
                lambda: self._queue_ai_fallback(ticket, text_for_prediction, prediction)
            )

        self._queue_created_email(ticket, user, category_name, priority, assignment_result)
        return ticket


TICKET_CREATION_SERVICE = TicketCreationService()


def create_ticket(validated_data, user):
    return TICKET_CREATION_SERVICE.create_ticket(validated_data, user)
