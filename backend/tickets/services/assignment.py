from django.db.models import Count, Q
from django.db import transaction
from tickets.models import Ticket
from users.models import AgentProfile


@transaction.atomic
def assign_ticket(ticket):

    category_name = ticket.category.name.strip().lower()

    agents = (
        AgentProfile.objects.filter(
            is_available=True,
            categories__name__iexact=category_name
        )
        .annotate(
            ticket_count=Count(
                'user__assigned_tickets',
                filter=Q(user__assigned_tickets__status='open')
            )
        )
        .order_by('ticket_count')
    )

    agent = min(
    agents,
    key=lambda a: a.user.assigned_tickets.count()
)

    if agent:
        ticket.assigned_to = agent.user
        ticket.save()
        return agent.user

    fallback = (
        AgentProfile.objects.filter(is_available=True)
        .annotate(ticket_count=Count('user__assigned_tickets'))
        .order_by('ticket_count')
        .first()
    )

    if fallback:
        ticket.assigned_to = fallback.user
        ticket.save()
        return fallback.user

    return None