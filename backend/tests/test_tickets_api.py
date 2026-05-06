from unittest.mock import patch

from rest_framework import status
from rest_framework.test import APITestCase

from tickets.models import Category, Ticket
from tickets.services.ticketcreate import create_ticket
from users.models import AgentProfile, User

from .test_utils import PASSWORD_FIELD, authenticate_client_with_jwt, build_test_password


class TicketApiTests(APITestCase):
    def setUp(self):
        self.admin_password = build_test_password()
        self.agent_password = build_test_password()
        self.other_agent_password = build_test_password()
        self.customer_password = build_test_password()
        self.other_customer_password = build_test_password()

        self.admin_user = User.objects.create_user(
            username="adminuser",
            email="admin@example.com",
            **{PASSWORD_FIELD: self.admin_password},
            role="admin",
        )
        self.agent_user = User.objects.create_user(
            username="agentuser",
            email="agent@example.com",
            **{PASSWORD_FIELD: self.agent_password},
            role="agent",
        )
        self.other_agent = User.objects.create_user(
            username="otheragent",
            email="otheragent@example.com",
            **{PASSWORD_FIELD: self.other_agent_password},
            role="agent",
        )
        self.customer_user = User.objects.create_user(
            username="customeruser",
            email="customer@example.com",
            **{PASSWORD_FIELD: self.customer_password},
            role="customer",
        )
        self.other_customer = User.objects.create_user(
            username="othercustomer",
            email="othercustomer@example.com",
            **{PASSWORD_FIELD: self.other_customer_password},
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
        self.predict_url = "/api/tickets/predict/"
        self.stats_url = "/api/tickets/stats/"
        self.prediction_stats_url = "/api/tickets/prediction-stats/"

    def test_predict_view_rejects_empty_text(self):
        authenticate_client_with_jwt(self.client, self.customer_user)
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
        authenticate_client_with_jwt(self.client, self.customer_user)
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
        self.assertEqual(response.data["results"][0]["id"], self.assigned_ticket.id)

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

    @patch("tickets.views.send_email_task.delay", side_effect=Exception("broker unavailable"))
    @patch("tickets.views.update_prediction_feedback")
    def test_ticket_update_succeeds_when_email_queue_fails(self, mock_feedback, mock_delay):
        self.client.force_authenticate(user=self.agent_user)
        response = self.client.patch(
            f"{self.ticket_list_url}{self.assigned_ticket.id}/",
            {"priority": Ticket.Priority.MEDIUM},
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assigned_ticket.refresh_from_db()
        self.assertEqual(self.assigned_ticket.priority, Ticket.Priority.MEDIUM)
        mock_feedback.assert_called_once()
        mock_delay.assert_not_called()

    @patch("tickets.views.send_email_task.delay")
    @patch("tickets.views.update_prediction_feedback")
    def test_ticket_update_without_status_change_does_not_queue_status_email(self, mock_feedback, mock_delay):
        self.client.force_authenticate(user=self.agent_user)
        response = self.client.patch(
            f"{self.ticket_list_url}{self.assigned_ticket.id}/",
            {"priority": Ticket.Priority.MEDIUM},
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assigned_ticket.refresh_from_db()
        self.assertEqual(self.assigned_ticket.priority, Ticket.Priority.MEDIUM)
        mock_feedback.assert_called_once()
        mock_delay.assert_not_called()

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

    def test_assign_ticket_rejects_empty_agent_id(self):
        self.client.force_authenticate(user=self.admin_user)
        response = self.client.patch(
            f"/api/tickets/{self.unassigned_ticket.id}/assign/",
            {"agent_id": ""},
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data["error"], "agent_id cannot be empty")

    def test_ticket_delete_is_not_available_for_admin(self):
        self.client.force_authenticate(user=self.admin_user)
        response = self.client.delete(f"{self.ticket_list_url}{self.unassigned_ticket.id}/", format="json")
        self.assertEqual(response.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)
        self.assertTrue(Ticket.objects.filter(id=self.unassigned_ticket.id).exists())

    def test_assign_ticket_returns_404_for_missing_ticket(self):
        self.client.force_authenticate(user=self.admin_user)
        response = self.client.patch(
            "/api/tickets/999999/assign/",
            {"agent_id": self.agent_user.id},
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        self.assertEqual(response.data["error"], "Ticket not found")

    def test_prediction_stats_requires_admin(self):
        self.client.force_authenticate(user=self.customer_user)
        response = self.client.get(self.prediction_stats_url, format="json")
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertIn("Only admins can view prediction stats.", str(response.data))

    @patch("tickets.services.ticketcreate.logger")
    @patch("tickets.services.ticketcreate.send_email_task.delay", side_effect=Exception("broker unavailable"))
    @patch("tickets.services.ticketcreate.auto_assign_ticket", return_value=({"assigned": False, "agent": None}, 200))
    @patch("tickets.services.ticketcreate.predict_ticket")
    @patch("tickets.services.ticketcreate.log_prediction")
    def test_create_ticket_succeeds_when_email_queue_fails(
        self,
        mock_log_prediction,
        mock_predict_ticket,
        _mock_auto_assign,
        _mock_delay,
        mock_logger,
    ):
        mock_predict_ticket.return_value = {
            "category": "network",
            "priority": "high",
            "confidence": 0.91,
            "source": "rules",
            "needs_manual_review": False,
        }

        ticket = create_ticket(
            {"title": "Email queue failure", "description": "Should still create"},
            self.customer_user,
        )

        self.assertIsNotNone(ticket.id)
        self.assertEqual(ticket.customer, self.customer_user)
        mock_log_prediction.assert_called_once()
        mock_logger.exception.assert_called_once()
