from rest_framework import status
from rest_framework.test import APITestCase

from tickets.models import Category, Ticket, TicketPredictionLog
from users.models import User

from .test_utils import PASSWORD_FIELD, build_test_password


class TicketPredictionApiTests(APITestCase):
    def setUp(self):
        self.admin_user = User.objects.create_user(
            username="pred-admin",
            email="pred-admin@example.com",
            **{PASSWORD_FIELD: build_test_password()},
            role="admin",
        )
        self.customer_user = User.objects.create_user(
            username="pred-customer",
            email="pred-customer@example.com",
            **{PASSWORD_FIELD: build_test_password()},
            role="customer",
        )
        self.other_customer = User.objects.create_user(
            username="pred-other-customer",
            email="pred-other@example.com",
            **{PASSWORD_FIELD: build_test_password()},
            role="customer",
        )
        self.agent_user = User.objects.create_user(
            username="pred-agent",
            email="pred-agent@example.com",
            **{PASSWORD_FIELD: build_test_password()},
            role="agent",
        )
        self.other_agent = User.objects.create_user(
            username="pred-other-agent",
            email="pred-other-agent@example.com",
            **{PASSWORD_FIELD: build_test_password()},
            role="agent",
        )
        self.category = Category.objects.create(name="network")
        self.assigned_ticket = Ticket.objects.create(
            title="Assigned issue",
            description="Assigned to agent",
            category=self.category,
            priority=Ticket.Priority.HIGH,
            customer=self.customer_user,
            assigned_to=self.agent_user,
            user_ticket_id=1,
        )
        self.other_ticket = Ticket.objects.create(
            title="Other customer issue",
            description="Owned by somebody else",
            category=self.category,
            priority=Ticket.Priority.LOW,
            customer=self.other_customer,
            assigned_to=self.other_agent,
            user_ticket_id=1,
        )
        self.prediction_stats_url = "/api/prediction-stats/"

    def test_prediction_stats_returns_accuracy_summary(self):
        TicketPredictionLog.objects.create(
            ticket=self.assigned_ticket,
            text="Assigned issue",
            predicted_category="network",
            predicted_priority="high",
            source="rules",
            confidence=0.9,
            actual_category="network",
            actual_priority="high",
            category_correct=True,
            priority_correct=True,
        )
        TicketPredictionLog.objects.create(
            ticket=self.other_ticket,
            text="Other issue",
            predicted_category="other",
            predicted_priority="low",
            source="ai",
            confidence=0.5,
            actual_category="billing",
            actual_priority="medium",
            category_correct=False,
            priority_correct=False,
        )
        self.client.force_authenticate(user=self.admin_user)
        response = self.client.get(self.prediction_stats_url, format="json")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["total_evaluated"], 2)
        self.assertEqual(response.data["category_accuracy"], 50.0)
        self.assertEqual(response.data["priority_accuracy"], 50.0)
        self.assertEqual(response.data["review_needed"], 1)

    def test_ticket_prediction_feedback_returns_latest_log(self):
        TicketPredictionLog.objects.create(
            ticket=self.assigned_ticket,
            text="Old prediction",
            predicted_category="hardware",
            predicted_priority="low",
            source="rules",
            confidence=0.4,
            actual_category="network",
            actual_priority="high",
            category_correct=False,
            priority_correct=False,
        )
        TicketPredictionLog.objects.create(
            ticket=self.assigned_ticket,
            text="Latest prediction",
            predicted_category="network",
            predicted_priority="high",
            source="ai",
            confidence=0.96,
            actual_category="network",
            actual_priority="high",
            category_correct=True,
            priority_correct=True,
        )
        self.client.force_authenticate(user=self.customer_user)
        response = self.client.get(
            f"/api/tickets/{self.assigned_ticket.id}/prediction-feedback/",
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data["has_feedback"])
        self.assertEqual(response.data["predicted_category"], "network")
        self.assertTrue(response.data["category_correct"])

    def test_ticket_prediction_feedback_forbids_other_customers(self):
        self.client.force_authenticate(user=self.customer_user)
        response = self.client.get(
            f"/api/tickets/{self.other_ticket.id}/prediction-feedback/",
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertIn("You can only view your own tickets.", str(response.data))
