from django.db import transaction
from django.db.models import Max

from tickets.ai import predict_ticket, log_prediction
from tickets.models import Ticket, Category
from tickets.services.assignment import auto_assign_ticket
from tickets.tasks import send_email_task


def create_ticket(validated_data, user):
    validated_data["customer"] = user

    prediction = predict_ticket(validated_data["description"])

    category_name = prediction["category"].lower().strip()
    priority = prediction["priority"].lower()

    category_obj, _ = Category.objects.get_or_create(name=category_name)

    validated_data["category"] = category_obj
    validated_data["priority"] = priority
    validated_data["predicted_category"] = category_name
    validated_data["predicted_priority"] = priority

    with transaction.atomic():
        last_id = (
            Ticket.objects
            .filter(customer=user)
            .select_for_update()
            .aggregate(Max("user_ticket_id"))["user_ticket_id__max"]
        )

        validated_data["user_ticket_id"] = (last_id or 0) + 1
        ticket = Ticket.objects.create(**validated_data)

        log_prediction(ticket.description, prediction, ticket)
        auto_assign_ticket(ticket)

    send_email_task.delay(
        ticket.customer.email,
        subject=f"Ticket '{ticket.title}' created successfully",
        template_name="emails/ticket_created.html",
        context={
            "customer_name": user.username,
            "ticket_title": ticket.title,
            "category": category_name,
            "priority": priority,
        }
    )

    return ticket