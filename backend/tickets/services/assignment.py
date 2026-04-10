from tickets.models import Ticket
from users.models import AgentProfile


def assign_ticket_to_agent(ticket, agent_id):
    try:
        profile = AgentProfile.objects.select_related("user").get(user__id=agent_id)
    except AgentProfile.DoesNotExist:
        return {"error": f"No AgentProfile found for user id {agent_id}"}, 404

    ticket.assigned_to = profile.user
    ticket.status = "in_progress"
    ticket.save()

    return {"message": f"Ticket assigned to {profile.user.username}"}, 200


def auto_assign_ticket(ticket):
    category_name = ticket.category.name if ticket.category else None

    if not category_name:
        return {"error": "Ticket has no category, cannot auto-assign"}, 400

    matching_profiles = (
        AgentProfile.objects
        .filter(is_available=True, categories__name__iexact=category_name)
        .select_related("user")
        .prefetch_related("categories")
        .distinct()
    )

    if not matching_profiles.exists():
        return {"error": "No available agents for this category"}, 404

    best_agent = min(
        matching_profiles,
        key=lambda profile: Ticket.objects.filter(
            assigned_to=profile.user,
            status__in=["open", "in_progress"]
        ).count()
    )

    ticket.assigned_to = best_agent.user
    ticket.status = "in_progress"
    ticket.save()

    return {
        "message": f"Auto-assigned to {best_agent.user.username}",
        "agent": best_agent.user.username
    }, 200