from django.db.models import Count
from django.db import transaction
from tickets.models import Agent


@transaction.atomic
def assign_ticket(ticket):
    agents = (
        Agent.objects.filter(
            is_active=True,
            agentcategory__category=ticket.category
        )
        .annotate(ticket_count=Count('tickets'))  # related_name='tickets'
        .order_by('ticket_count')
    )

    for agent in agents:
        if agent.ticket_count < agent.max_tickets:
            ticket.assigned_to = agent
            ticket.status = "assigned"
            ticket.save()
            return agent

    # No agent available
    ticket.status = "unassigned"
    ticket.save()
    return None