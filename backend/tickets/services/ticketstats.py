import logging
from datetime import timedelta

from django.db.models import Q, Count, Avg, F, ExpressionWrapper, DurationField
from django.db.models.functions import TruncDate
from django.utils import timezone

from tickets.models import Ticket
from users.models import AgentProfile

logger = logging.getLogger(__name__)


class TicketStatsService:
    def _queryset_for_user(self, user):
        role = user.role.lower()
        if role == "admin":
            return role, Ticket.objects.all()
        if role == "agent":
            return role, Ticket.objects.filter(assigned_to=user)
        return role, Ticket.objects.filter(customer=user)

    def _agent_workload(self):
        agent_profiles = AgentProfile.objects.select_related("user").all()
        agent_workload = []

        for profile in agent_profiles:
            agent_tickets = Ticket.objects.filter(assigned_to=profile.user)
            assigned = agent_tickets.count()
            in_progress = agent_tickets.filter(status="in_progress").count()
            solved = agent_tickets.filter(status="closed").count()

            avg_resolution = agent_tickets.filter(status="closed").aggregate(
                avg=Avg(
                    ExpressionWrapper(
                        F("updated_at") - F("created_at"),
                        output_field=DurationField()
                    )
                )
            )["avg"]

            avg_hours = round(avg_resolution.total_seconds() / 3600, 1) if avg_resolution else None
            agent_workload.append({
                "agent": profile.user.username,
                "assigned": assigned,
                "in_progress": in_progress,
                "solved": solved,
                "avg_resolution_hours": avg_hours,
            })

        agent_workload.sort(key=lambda x: x["assigned"], reverse=True)
        return agent_workload

    def build_ticket_stats(self, user):
        try:
            role, queryset = self._queryset_for_user(user)

            stats = queryset.aggregate(
                total=Count("id"),
                open=Count("id", filter=Q(status="open")),
                in_progress=Count("id", filter=Q(status="in_progress")),
                closed=Count("id", filter=Q(status="closed")),
            )

            if role == "admin":
                by_category = list(
                    queryset.values("category__name")
                    .annotate(count=Count("id"))
                    .order_by("-count")
                )

                by_priority = list(
                    queryset.values("priority")
                    .annotate(count=Count("id"))
                    .order_by("-count")
                )

                seven_days_ago = timezone.now() - timedelta(days=7)
                by_date = list(
                    queryset
                    .filter(created_at__gte=seven_days_ago)
                    .annotate(date=TruncDate("created_at"))
                    .values("date")
                    .annotate(count=Count("id"))
                    .order_by("date")
                )

                for entry in by_date:
                    entry["date"] = str(entry["date"])

                stats["by_category"] = by_category
                stats["by_priority"] = by_priority
                stats["by_date"] = by_date
                stats["agent_workload"] = self._agent_workload()

            return stats, 200

        except Exception as error:
            logger.exception("Failed to build ticket stats for user_id=%s", getattr(user, "id", None))
            return {"error": str(error)}, 500


TICKET_STATS_SERVICE = TicketStatsService()


def build_ticket_stats(user):
    return TICKET_STATS_SERVICE.build_ticket_stats(user)
