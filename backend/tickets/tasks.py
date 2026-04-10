from celery import shared_task
from django.template.loader import render_to_string
from django.conf import settings
import requests
import logging

logger = logging.getLogger(__name__)


@shared_task(bind=True, max_retries=3, default_retry_delay=60)
def send_email_task(self, recipient_email, subject, template_name="emails/ticket_created.html", context=None):
    try:
        context = context or {}

        # Render HTML template
        html_content = render_to_string(template_name, context)

        # Brevo API call
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
            raise Exception(
                f"Brevo API error {response.status_code}: {response.text}"
            )

        logger.info(f"✅ Email sent → {recipient_email}")

    except Exception as exc:
        logger.error(
            f"❌ Email failed (attempt {self.request.retries + 1}): {exc}",
            exc_info=True,
        )
        raise self.retry(exc=exc)