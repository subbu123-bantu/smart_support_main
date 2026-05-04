import logging

import requests
from celery import shared_task
from django.conf import settings
from django.template.loader import render_to_string

from tickets.exceptions import EmailSendError

logger = logging.getLogger(__name__)


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
