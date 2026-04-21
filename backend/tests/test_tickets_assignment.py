from django.test import TestCase

from tickets.models import Category, Ticket
from tickets.services.assignment import assign_ticket_to_agent, auto_assign_ticket
from users.models import AgentProfile, User

from .test_utils import PASSWORD_FIELD, build_test_password


class TicketAssignmentServiceTests(TestCase):
    def setUp(self):
        self.customer = User.objects.create_user(
            username="svc-customer",
            email="svc-customer@example.com",
            **{PASSWORD_FIELD: build_test_password()},
            role="customer",
        )
        self.agent_one = User.objects.create_user(
            username="svc-agent-one",
            email="svc-agent-one@example.com",
            **{PASSWORD_FIELD: build_test_password()},
            role="agent",
        )
        self.agent_two = User.objects.create_user(
            username="svc-agent-two",
            email="svc-agent-two@example.com",
            **{PASSWORD_FIELD: build_test_password()},
            role="agent",
        )
        self.network = Category.objects.create(name="network")
        self.agent_one_profile = AgentProfile.objects.create(user=self.agent_one, is_available=True)
        self.agent_two_profile = AgentProfile.objects.create(user=self.agent_two, is_available=True)
        self.agent_one_profile.categories.add(self.network)
        self.agent_two_profile.categories.add(self.network)
        self.ticket = Ticket.objects.create(
            title="Needs assignment",
            description="Please assign me",
            category=self.network,
            customer=self.customer,
            user_ticket_id=1,
        )
        Ticket.objects.create(
            title="Existing workload",
            description="Already on agent one",
            category=self.network,
            customer=self.customer,
            assigned_to=self.agent_one,
            status=Ticket.Status.OPEN,
            user_ticket_id=2,
        )

    def test_assign_ticket_to_agent_returns_error_for_missing_profile(self):
        payload, status_code = assign_ticket_to_agent(self.ticket, 999999)
        self.assertEqual(status_code, 404)
        self.assertIn("No AgentProfile found", payload["error"])

    def test_assign_ticket_to_agent_updates_ticket_and_returns_agent_name(self):
        payload, status_code = assign_ticket_to_agent(self.ticket, self.agent_one.id)
        self.assertEqual(status_code, 200)
        self.ticket.refresh_from_db()
        self.assertEqual(self.ticket.assigned_to, self.agent_one)
        self.assertEqual(self.ticket.status, Ticket.Status.IN_PROGRESS)
        self.assertEqual(payload["agent"], self.agent_one.username)

    def test_auto_assign_ticket_returns_missing_category_when_ticket_has_no_category(self):
        self.ticket.category = None
        payload, status_code = auto_assign_ticket(self.ticket)
        self.assertEqual(status_code, 200)
        self.assertEqual(payload, {"assigned": False, "reason": "missing_category"})

    def test_auto_assign_ticket_returns_no_available_agent_when_no_profile_matches(self):
        self.agent_one_profile.categories.clear()
        self.agent_two_profile.categories.clear()
        payload, status_code = auto_assign_ticket(self.ticket)
        self.assertEqual(status_code, 200)
        self.assertEqual(payload, {"assigned": False, "reason": "no_available_agent"})

    def test_auto_assign_ticket_prefers_agent_with_lowest_active_ticket_count(self):
        payload, status_code = auto_assign_ticket(self.ticket)
        self.assertEqual(status_code, 200)
        self.ticket.refresh_from_db()
        self.assertTrue(payload["assigned"])
        self.assertEqual(payload["agent"], self.agent_two.username)
        self.assertEqual(payload["active_ticket_count"], 0)
        self.assertEqual(self.ticket.assigned_to, self.agent_two)
        self.assertEqual(self.ticket.status, Ticket.Status.IN_PROGRESS)
