from rest_framework import status
from rest_framework.test import APITestCase

from tickets.models import Ticket, TicketPredictionLog

from .test_utils import make_category, make_prediction_log, make_ticket, make_user


class TicketPredictionApiTests(APITestCase):
    def setUp(self):
        self.admin_user = make_user(role="admin", username="pred-admin")
        self.customer_user = make_user(role="customer", username="pred-customer")
        self.other_customer = make_user(role="customer", username="pred-other-customer")
        self.agent_user = make_user(role="agent", username="pred-agent")
        self.other_agent = make_user(role="agent", username="pred-other-agent")
        self.category = make_category("network")
        self.assigned_ticket = make_ticket(
            title="Assigned issue",
            description="Assigned to agent",
            category=self.category,
            priority=Ticket.Priority.HIGH,
            customer=self.customer_user,
            assigned_to=self.agent_user,
            user_ticket_id=1,
        )
        self.other_ticket = make_ticket(
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
        make_prediction_log(
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
        make_prediction_log(
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

    def test_prediction_stats_forbids_non_admin_users(self):
        self.client.force_authenticate(user=self.customer_user)
        response = self.client.get(self.prediction_stats_url, format="json")
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertIn("Only admins can view prediction stats.", str(response.data))

    def test_ticket_prediction_feedback_returns_latest_log(self):
        make_prediction_log(
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
        make_prediction_log(
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
