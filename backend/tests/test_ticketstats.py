from datetime import timedelta
from types import SimpleNamespace

from django.test import TestCase
from django.utils import timezone

from tickets.models import Ticket
from tickets.services.ticketstats import build_ticket_stats

from .test_utils import make_agent_profile, make_category, make_ticket, make_user


class TicketStatsServiceTests(TestCase):
    def setUp(self):
        self.admin = make_user(role="admin", username="admin-stats")
        self.agent = make_user(role="agent", username="agent-stats")
        self.customer = make_user(role="customer", username="customer-stats")
        self.other_customer = make_user(role="customer", username="other-customer-stats")

        self.hardware = make_category("Hardware")
        self.billing = make_category("Billing")

        make_agent_profile(self.agent)

        self.agent_closed_ticket = make_ticket(
            title="Closed agent ticket",
            category=self.hardware,
            customer=self.customer,
            assigned_to=self.agent,
            priority=Ticket.Priority.HIGH,
            status=Ticket.Status.CLOSED,
            user_ticket_id=101,
        )
        Ticket.objects.filter(pk=self.agent_closed_ticket.pk).update(
            created_at=timezone.now() - timedelta(hours=5),
            updated_at=timezone.now() - timedelta(hours=1),
        )

        self.agent_open_ticket = make_ticket(
            title="Open agent ticket",
            category=self.hardware,
            customer=self.customer,
            assigned_to=self.agent,
            priority=Ticket.Priority.URGENT,
            status=Ticket.Status.IN_PROGRESS,
            user_ticket_id=102,
        )

        self.customer_ticket = make_ticket(
            title="Customer ticket",
            category=self.billing,
            customer=self.customer,
            priority=Ticket.Priority.LOW,
            status=Ticket.Status.OPEN,
            user_ticket_id=103,
        )

        self.other_customer_ticket = make_ticket(
            title="Other customer ticket",
            category=self.billing,
            customer=self.other_customer,
            priority=Ticket.Priority.MEDIUM,
            status=Ticket.Status.OPEN,
            user_ticket_id=104,
        )

    def test_build_ticket_stats_returns_admin_breakdowns_and_workload(self):
        stats, status_code = build_ticket_stats(self.admin)

        self.assertEqual(status_code, 200)
        self.assertEqual(stats["total"], 4)
        self.assertEqual(stats["open"], 2)
        self.assertEqual(stats["in_progress"], 1)
        self.assertEqual(stats["closed"], 1)

        self.assertIn({"category__name": "Hardware", "count": 2}, stats["by_category"])
        self.assertIn({"priority": Ticket.Priority.HIGH, "count": 1}, stats["by_priority"])
        self.assertTrue(any(entry["date"] for entry in stats["by_date"]))

        self.assertEqual(len(stats["agent_workload"]), 1)
        workload = stats["agent_workload"][0]
        self.assertEqual(workload["agent"], self.agent.username)
        self.assertEqual(workload["assigned"], 2)
        self.assertEqual(workload["in_progress"], 1)
        self.assertEqual(workload["solved"], 1)
        self.assertEqual(workload["avg_resolution_hours"], 4.0)

    def test_build_ticket_stats_filters_for_agent_and_customer(self):
        agent_stats, agent_status_code = build_ticket_stats(self.agent)
        customer_stats, customer_status_code = build_ticket_stats(self.customer)

        self.assertEqual(agent_status_code, 200)
        self.assertEqual(agent_stats, {"total": 2, "open": 0, "in_progress": 1, "closed": 1})

        self.assertEqual(customer_status_code, 200)
        self.assertEqual(customer_stats, {"total": 3, "open": 1, "in_progress": 1, "closed": 1})

    def test_build_ticket_stats_returns_500_payload_on_unexpected_error(self):
        broken_user = SimpleNamespace(id=999, role=None)

        payload, status_code = build_ticket_stats(broken_user)

        self.assertEqual(status_code, 500)
        self.assertIn("error", payload)
