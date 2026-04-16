from unittest.mock import patch

from django.test import TestCase
from rest_framework import status
from rest_framework.test import APITestCase

from tickets.models import Category, Ticket, TicketComment, TicketPredictionLog
from tickets.services.ticketcomments import create_comment_for_user, get_comment_queryset_for_user
from users.models import AgentProfile, User


class TicketApiTests(APITestCase):
    def setUp(self):
        self.admin_user = User.objects.create_user(
            username="adminuser",
            email="admin@example.com",
            password="AdminPass123!",
            role="admin",
        )
        self.agent_user = User.objects.create_user(
            username="agentuser",
            email="agent@example.com",
            password="AgentPass123!",
            role="agent",
        )
        self.other_agent = User.objects.create_user(
            username="otheragent",
            email="otheragent@example.com",
            password="OtherAgent123!",
            role="agent",
        )
        self.customer_user = User.objects.create_user(
            username="customeruser",
            email="customer@example.com",
            password="CustomerPass123!",
            role="customer",
        )
        self.other_customer = User.objects.create_user(
            username="othercustomer",
            email="othercustomer@example.com",
            password="OtherCustomer123!",
            role="customer",
        )

        self.category = Category.objects.create(name="network")
        AgentProfile.objects.create(user=self.agent_user, is_available=True)
        AgentProfile.objects.create(user=self.other_agent, is_available=True)

        self.unassigned_ticket = Ticket.objects.create(
            title="Unassigned issue",
            description="Needs attention",
            category=self.category,
            priority=Ticket.Priority.MEDIUM,
            customer=self.customer_user,
            user_ticket_id=1,
        )
        self.assigned_ticket = Ticket.objects.create(
            title="Assigned issue",
            description="Assigned to agent",
            category=self.category,
            priority=Ticket.Priority.HIGH,
            status=Ticket.Status.OPEN,
            customer=self.customer_user,
            assigned_to=self.agent_user,
            user_ticket_id=2,
        )
        self.other_ticket = Ticket.objects.create(
            title="Other customer issue",
            description="Owned by somebody else",
            category=self.category,
            priority=Ticket.Priority.LOW,
            status=Ticket.Status.CLOSED,
            customer=self.other_customer,
            assigned_to=self.other_agent,
            user_ticket_id=1,
        )

        self.ticket_list_url = "/api/tickets/"
        self.predict_url = "/api/predict/"
        self.stats_url = "/api/stats/"
        self.prediction_stats_url = "/api/prediction-stats/"

    def test_predict_view_rejects_empty_text(self):
        self.client.force_authenticate(user=self.customer_user)

        response = self.client.post(self.predict_url, {"text": "   "}, format="json")

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data["detail"], "Text is required")

    @patch("tickets.views.predict_ticket")
    def test_predict_view_returns_prediction_payload(self, mock_predict_ticket):
        mock_predict_ticket.return_value = {
            "category": "network",
            "priority": "high",
            "confidence": 0.91,
            "source": "rules",
            "needs_manual_review": False,
        }
        self.client.force_authenticate(user=self.customer_user)

        response = self.client.post(self.predict_url, {"text": "Router is down"}, format="json")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["predicted_category"], "network")
        self.assertEqual(response.data["predicted_priority"], "high")
        self.assertEqual(response.data["category_confidence"], 0.91)

    def test_ticket_list_for_admin_filters_assigned_false(self):
        self.client.force_authenticate(user=self.admin_user)

        response = self.client.get(f"{self.ticket_list_url}?assigned=false", format="json")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        results = response.data["results"]
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0]["id"], self.unassigned_ticket.id)

    def test_ticket_list_for_agent_returns_only_assigned_tickets(self):
        self.client.force_authenticate(user=self.agent_user)

        response = self.client.get(self.ticket_list_url, format="json")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        results = response.data["results"]
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0]["id"], self.assigned_ticket.id)

    def test_ticket_list_for_customer_returns_only_own_tickets(self):
        self.client.force_authenticate(user=self.customer_user)

        response = self.client.get(self.ticket_list_url, format="json")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        returned_ids = {item["id"] for item in response.data["results"]}
        self.assertEqual(returned_ids, {self.unassigned_ticket.id, self.assigned_ticket.id})

    def test_ticket_create_forbids_non_customers(self):
        self.client.force_authenticate(user=self.agent_user)

        response = self.client.post(
            self.ticket_list_url,
            {
                "title": "Agent cannot create",
                "description": "Should be blocked",
                "category": self.category.id,
                "priority": Ticket.Priority.LOW,
            },
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertIn("Only customers can create tickets.", str(response.data))

    @patch("tickets.views.send_email_task.delay")
    @patch("tickets.views.update_prediction_feedback")
    def test_ticket_update_allows_assigned_agent_status_change(self, mock_feedback, mock_delay):
        self.client.force_authenticate(user=self.agent_user)

        response = self.client.patch(
            f"{self.ticket_list_url}{self.assigned_ticket.id}/",
            {"status": Ticket.Status.IN_PROGRESS},
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assigned_ticket.refresh_from_db()
        self.assertEqual(self.assigned_ticket.status, Ticket.Status.IN_PROGRESS)
        mock_feedback.assert_called_once()
        mock_delay.assert_called_once()

    def test_ticket_update_blocks_agent_from_editing_disallowed_fields(self):
        self.client.force_authenticate(user=self.agent_user)

        response = self.client.patch(
            f"{self.ticket_list_url}{self.assigned_ticket.id}/",
            {"title": "New title"},
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertIn("Agents can only update ticket status and priority.", str(response.data))

    def test_ticket_stats_returns_admin_aggregates(self):
        self.client.force_authenticate(user=self.admin_user)

        response = self.client.get(self.stats_url, format="json")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["total"], 3)
        self.assertEqual(response.data["open"], 2)
        self.assertEqual(response.data["closed"], 1)
        self.assertIn("by_category", response.data)
        self.assertIn("by_priority", response.data)
        self.assertIn("agent_workload", response.data)

    def test_assign_ticket_requires_admin(self):
        self.client.force_authenticate(user=self.customer_user)

        response = self.client.patch(
            f"/api/tickets/{self.unassigned_ticket.id}/assign/",
            {"agent_id": self.agent_user.id},
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertIn("Only admins can assign tickets.", str(response.data))

    def test_assign_ticket_with_agent_id_assigns_ticket(self):
        self.client.force_authenticate(user=self.admin_user)

        response = self.client.patch(
            f"/api/tickets/{self.unassigned_ticket.id}/assign/",
            {"agent_id": self.agent_user.id},
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.unassigned_ticket.refresh_from_db()
        self.assertEqual(self.unassigned_ticket.assigned_to, self.agent_user)
        self.assertEqual(self.unassigned_ticket.status, Ticket.Status.IN_PROGRESS)

    def test_assign_ticket_returns_404_for_missing_ticket(self):
        self.client.force_authenticate(user=self.admin_user)

        response = self.client.patch(
            "/api/tickets/999999/assign/",
            {"agent_id": self.agent_user.id},
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        self.assertEqual(response.data["error"], "Ticket not found")

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


class TicketCommentServiceTests(TestCase):
    def setUp(self):
        self.admin_user = User.objects.create_user(
            username="admincomments",
            email="admincomments@example.com",
            password="AdminPass123!",
            role="admin",
        )
        self.agent_user = User.objects.create_user(
            username="agentcomments",
            email="agentcomments@example.com",
            password="AgentPass123!",
            role="agent",
        )
        self.customer_user = User.objects.create_user(
            username="customercomments",
            email="customercomments@example.com",
            password="CustomerPass123!",
            role="customer",
        )
        self.other_customer = User.objects.create_user(
            username="othercomments",
            email="othercomments@example.com",
            password="OtherCustomer123!",
            role="customer",
        )

        self.category = Category.objects.create(name="hardware")
        self.ticket = Ticket.objects.create(
            title="Commented ticket",
            description="Comment service coverage",
            category=self.category,
            customer=self.customer_user,
            assigned_to=self.agent_user,
            user_ticket_id=1,
        )

        self.public_comment = TicketComment.objects.create(
            ticket=self.ticket,
            user=self.agent_user,
            message="Visible to customer",
            is_internal=False,
        )
        self.internal_comment = TicketComment.objects.create(
            ticket=self.ticket,
            user=self.admin_user,
            message="Internal only",
            is_internal=True,
        )

    def test_get_comment_queryset_for_customer_hides_internal_comments(self):
        queryset = get_comment_queryset_for_user(self.customer_user, self.ticket)

        self.assertEqual(list(queryset), [self.public_comment])

    @patch("tickets.services.ticketcomments.send_email_task.delay")
    def test_create_comment_for_customer_forces_non_internal(self, mock_delay):
        class DummySerializer:
            def save(self, **kwargs):
                return TicketComment.objects.create(message="Customer reply", **kwargs)

        comment = create_comment_for_user(DummySerializer(), self.customer_user, self.ticket)

        self.assertFalse(comment.is_internal)
        mock_delay.assert_not_called()
