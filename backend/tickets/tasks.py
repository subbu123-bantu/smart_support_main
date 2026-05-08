import logging

import requests
from asgiref.sync import async_to_sync
from celery import shared_task
from django.conf import settings
from django.template.loader import render_to_string

from tickets.ai.ai import log_prediction, predict_ticket
from tickets.exceptions import EmailSendError
from tickets.models import Category, Ticket
logger = logging.getLogger(__name__)


def _apply_prediction_to_ticket(ticket, prediction):
    changed_fields = set()
    predicted_category = prediction["category"]
    predicted_priority = prediction["priority"]

    if ticket.predicted_category != predicted_category:
        ticket.predicted_category = predicted_category
        changed_fields.add("predicted_category")

    if ticket.predicted_priority != predicted_priority:
        ticket.predicted_priority = predicted_priority
        changed_fields.add("predicted_priority")

    has_placeholder_category = (
        ticket.category is None or ticket.category.name.lower() == "other"
    )
    if predicted_category != "other" and has_placeholder_category:
        category_obj, _ = Category.objects.get_or_create(name=predicted_category)
        ticket.category = category_obj
        ticket.priority = predicted_priority
        changed_fields.update({"category", "priority"})

    if changed_fields:
        ticket.save(update_fields=sorted(changed_fields | {"updated_at"}))

    return bool(changed_fields)


@shared_task(bind=True, max_retries=5)
def send_email_task(
    self,
    recipient_email,
    subject,
    template_name="emails/ticket_created.html",
    context=None,
):
    try:
        context = context or {}
        html_content = render_to_string(template_name, context)

        response = requests.post(
            "https://api.brevo.com/v3/smtp/email",
            headers={
                "api-key": settings.BREVO_API_KEY,
                "Content-Type": "application/json",
            },
            json={
                "sender": {
                    "name": "Support Team",
                    "email": settings.DEFAULT_FROM_EMAIL,
                },
                "to": [{"email": recipient_email}],
                "subject": subject,
                "htmlContent": html_content,
            },
            timeout=10,
        )

        if response.status_code not in (200, 201):
            raise EmailSendError(
                status_code=response.status_code,
                message=response.text,
            )

        logger.info("Email sent to %s", recipient_email)

    except (requests.RequestException, EmailSendError) as exc:
        retry_count = self.request.retries + 1
        countdown = min(60 * (2 ** self.request.retries), 300)

        logger.error(
            "Email failed (attempt %s/%s): %s",
            retry_count,
            self.max_retries + 1,
            exc,
            exc_info=True,
        )

        if self.request.retries >= self.max_retries:
            logger.error("Email permanently failed for %s", recipient_email)
            raise

        raise self.retry(exc=exc, countdown=countdown)


@shared_task(bind=True, max_retries=3)
def run_ai_fallback_prediction_task(self, ticket_id, text):
    """
    Runs the slower AI-assisted prediction away from the request thread.
    This keeps ticket creation synchronous for immediate assignment while
    still allowing richer prediction data to arrive shortly after creation.
    """
    try:
        from tickets.services.assignment import auto_assign_ticket

        ticket = Ticket.objects.select_related("category").get(id=ticket_id)
        prediction = async_to_sync(predict_ticket)(text)
        log_prediction(text, prediction, ticket)
        _apply_prediction_to_ticket(ticket, prediction)

        if ticket.assigned_to_id is None and ticket.category_id:
            auto_assign_ticket(ticket)

        logger.info(
            "AI fallback prediction completed for ticket_id=%s source=%s",
            ticket_id,
            prediction["source"],
        )
    except Ticket.DoesNotExist:
        logger.warning("Skipping AI fallback prediction; ticket_id=%s no longer exists", ticket_id)
    except Exception as exc:
        retry_count = self.request.retries + 1
        countdown = min(30 * (2 ** self.request.retries), 300)
        logger.error(
            "AI fallback prediction failed (attempt %s/%s) for ticket_id=%s: %s",
            retry_count,
            self.max_retries + 1,
            ticket_id,
            exc,
            exc_info=True,
        )
        if self.request.retries >= self.max_retries:
            raise
        raise self.retry(exc=exc, countdown=countdown)
