from django.db.models import Count, Q
from django.db import transaction
from tickets.models import Ticket
from users.models import AgentProfile


@transaction.atomic
def assign_ticket(ticket):

    category_name = ticket.category.name.strip().lower()

    # Try to find available agent matching the ticket's category
    agent_profile = (
        AgentProfile.objects.filter(
            is_available=True,
            categories__name__iexact=category_name
        )
        .annotate(
            ticket_count=Count(
                'user__assigned_tickets',
                filter=Q(user__assigned_tickets__status__in=['open', 'in_progress'])
            )
        )
        .order_by('ticket_count')
        .first()  # just take the first (least busy) — no min() needed
    )

    if agent_profile:
        ticket.assigned_to = agent_profile.user
        ticket.save()
        return agent_profile.user

    # Fallback — assign to any available agent regardless of category
    fallback = (
        AgentProfile.objects.filter(is_available=True)
        .annotate(
            ticket_count=Count(
                'user__assigned_tickets',
                filter=Q(user__assigned_tickets__status__in=['open', 'in_progress'])
            )
        )
        .order_by('ticket_count')
        .first()
    )

    if fallback:
        ticket.assigned_to = fallback.user
        ticket.save()
        return fallback.user

    return None