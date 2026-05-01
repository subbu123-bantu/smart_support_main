from django.db.models import Count, Q

from tickets.models import Ticket
from users.models import AgentProfile


class TicketAssignmentService:
    def _apply_assignment(self, ticket, user):
        ticket.assigned_to = user
        ticket.status = Ticket.Status.IN_PROGRESS
        ticket.save(update_fields=["assigned_to", "status", "updated_at"])

    def assign_ticket_to_agent(self, ticket, agent_id):
        try:
            profile = AgentProfile.objects.select_related("user").filter(user__role__iexact="agent").get(user__id=agent_id)
        except AgentProfile.DoesNotExist:
            return {"error": f"No AgentProfile found for user id {agent_id}"}, 404

        self._apply_assignment(ticket, profile.user)
        return {
            "message": f"Ticket assigned to {profile.user.username}",
            "agent": profile.user.username,
        }, 200

    def auto_assign_ticket(self, ticket):
        category_name = ticket.category.name if ticket.category else None

        if not category_name:
            return {"assigned": False, "reason": "missing_category"}, 200

        matching_profiles = (
            AgentProfile.objects
            .filter(is_available=True, categories__name__iexact=category_name)
            .select_related("user")
            .annotate(
                active_ticket_count=Count(
                    "user__assigned_tickets",
                    filter=Q(
                        user__assigned_tickets__status__in=[
                            Ticket.Status.OPEN,
                            Ticket.Status.IN_PROGRESS,
                        ]
                    ),
                )
            )
            .order_by("active_ticket_count", "user__username")
            .distinct()
        )

        best_agent = matching_profiles.first()

        if not best_agent:
            return {"assigned": False, "reason": "no_available_agent"}, 200

        self._apply_assignment(ticket, best_agent.user)
        return {
            "assigned": True,
            "message": f"Auto-assigned to {best_agent.user.username}",
            "agent": best_agent.user.username,
            "active_ticket_count": best_agent.active_ticket_count,
        }, 200


ASSIGNMENT_SERVICE = TicketAssignmentService()


def assign_ticket_to_agent(ticket, agent_id):
    return ASSIGNMENT_SERVICE.assign_ticket_to_agent(ticket, agent_id)


def auto_assign_ticket(ticket):
    return ASSIGNMENT_SERVICE.auto_assign_ticket(ticket)
