from django.utils.crypto import get_random_string

from tickets.models import Category, Ticket, TicketPredictionLog
from users.models import AgentProfile, User


PASSWORD_FIELD = "password"


def build_test_password():
    return f"test-{get_random_string(16)}-Aa1!"


def make_user(*, role="customer", username=None, email=None, password=None, **extra_fields):
    username = username or f"{role}-{get_random_string(8)}"
    email = email or f"{username}@example.com"
    password = password or build_test_password()
    user = User.objects.create_user(
        username=username,
        email=email,
        **{PASSWORD_FIELD: password},
        role=role,
        **extra_fields,
    )
    user.raw_password = password
    return user


def make_category(name=None):
    name = name or f"category-{get_random_string(8)}"
    return Category.objects.create(name=name)


def make_agent_profile(user, *, is_available=True, categories=None):
    profile = AgentProfile.objects.create(user=user, is_available=is_available)
    if categories:
        profile.categories.add(*categories)
    return profile


def make_ticket(
    *,
    title="Test ticket",
    description="Test description",
    category=None,
    customer,
    assigned_to=None,
    priority=Ticket.Priority.MEDIUM,
    status=Ticket.Status.OPEN,
    user_ticket_id=1,
    **extra_fields,
):
    category = category or make_category()
    return Ticket.objects.create(
        title=title,
        description=description,
        category=category,
        customer=customer,
        assigned_to=assigned_to,
        priority=priority,
        status=status,
        user_ticket_id=user_ticket_id,
        **extra_fields,
    )


def make_prediction_log(
    *,
    ticket=None,
    text="Predicted issue",
    predicted_category="network",
    predicted_priority="medium",
    source="rules",
    confidence=0.5,
    **extra_fields,
):
    return TicketPredictionLog.objects.create(
        ticket=ticket,
        text=text,
        predicted_category=predicted_category,
        predicted_priority=predicted_priority,
        source=source,
        confidence=confidence,
        **extra_fields,
    )
