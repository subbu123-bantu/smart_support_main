from django.db.models import Count, Q
from tickets.models import Ticket
from users.models import AgentProfile   # adjust import if needed


def assign_ticket(ticket):
    """
    Assign ticket to least-loaded available agent
    based on category match
    """

    # Step 1: filter agents by availability + category
    agents = AgentProfile.objects.filter(
        is_available=True,
        categories=ticket.category
    ).annotate(
        # Step 2: count only OPEN tickets assigned to that agent
        ticket_count=Count(
            'user__assigned_tickets',
            filter=Q(user__assigned_tickets__status='open')
        )
    ).order_by('ticket_count')

    # Step 3: pick least loaded agent
    agent = agents.first()

    if agent:
        # Step 4: assign ticket to that agent's USER
        ticket.assigned_to = agent.user
        ticket.save()
        return agent.user

    return None