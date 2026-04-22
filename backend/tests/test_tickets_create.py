from unittest.mock import patch

from django.test import TestCase

from tickets.models import Ticket
from tickets.services.ticketcreate import create_ticket
from users.models import User

from .test_utils import PASSWORD_FIELD, build_test_password


class TicketCreateServiceTests(TestCase):
    def setUp(self):
        self.customer = User.objects.create_user(
            username="create-customer",
            email="create-customer@example.com",
            **{PASSWORD_FIELD: build_test_password()},
            role="customer",
        )
        self.agent = User.objects.create_user(
            username="create-agent",
            email="create-agent@example.com",
            **{PASSWORD_FIELD: build_test_password()},
            role="agent",
        )

    @patch("tickets.services.ticketcreate.send_email_task.delay")
    @patch("tickets.services.ticketcreate.auto_assign_ticket")
    @patch("tickets.services.ticketcreate.log_prediction")
    @patch("tickets.services.ticketcreate.predict_ticket")
    def test_create_ticket_uses_prediction_and_auto_assignment(self, mock_predict_ticket, mock_log_prediction, mock_auto_assign, mock_send_email):
        mock_predict_ticket.return_value = {
            "category": "Network ",
            "priority": "HIGH",
            "confidence": 0.88,
            "source": "ai",
        }
        mock_auto_assign.return_value = ({"assigned": True, "agent": self.agent.username}, 200)
        ticket = create_ticket({"title": "Router issue", "description": "Router is down"}, self.customer)
        ticket.refresh_from_db()
        self.assertEqual(ticket.customer, self.customer)
        self.assertEqual(ticket.category.name, "network")
        self.assertEqual(ticket.priority, Ticket.Priority.HIGH)
        self.assertEqual(ticket.predicted_category, "network")
        self.assertEqual(ticket.predicted_priority, Ticket.Priority.HIGH)
        self.assertEqual(ticket.user_ticket_id, 1)
        mock_log_prediction.assert_called_once()
        mock_auto_assign.assert_called_once_with(ticket)
        mock_send_email.assert_called_once()

    @patch("tickets.services.ticketcreate.send_email_task.delay")
    @patch("tickets.services.ticketcreate.auto_assign_ticket", side_effect=RuntimeError("assignment failed"))
    @patch("tickets.services.ticketcreate.log_prediction")
    @patch("tickets.services.ticketcreate.predict_ticket")
    def test_create_ticket_still_sends_email_when_auto_assignment_fails(self, mock_predict_ticket, mock_log_prediction, mock_auto_assign, mock_send_email):
        mock_predict_ticket.return_value = {
            "category": "Billing",
            "priority": "low",
            "confidence": 0.55,
            "source": "rules",
        }
        ticket = create_ticket({"title": "Billing issue", "description": "Need invoice help"}, self.customer)
        self.assertEqual(ticket.user_ticket_id, 1)
        mock_log_prediction.assert_called_once()
        mock_auto_assign.assert_called_once_with(ticket)
        _, kwargs = mock_send_email.call_args
        self.assertFalse(kwargs["context"]["assigned"])
        self.assertIsNone(kwargs["context"]["assigned_agent"])

    @patch("tickets.services.ticketcreate.send_email_task.delay")
    @patch("tickets.services.ticketcreate.auto_assign_ticket")
    @patch("tickets.services.ticketcreate.log_prediction")
    @patch("tickets.services.ticketcreate.predict_ticket")
    def test_create_ticket_increments_user_ticket_id_per_customer(self, mock_predict_ticket, mock_log_prediction, mock_auto_assign, mock_send_email):
        mock_predict_ticket.return_value = {
            "category": "Account",
            "priority": "medium",
            "confidence": 0.73,
            "source": "ai",
        }
        mock_auto_assign.return_value = ({"assigned": False, "agent": None}, 200)
        first_ticket = create_ticket({"title": "First issue", "description": "First description"}, self.customer)
        second_ticket = create_ticket({"title": "Second issue", "description": "Second description"}, self.customer)
        self.assertEqual(first_ticket.user_ticket_id, 1)
        self.assertEqual(second_ticket.user_ticket_id, 2)
        self.assertEqual(mock_log_prediction.call_count, 2)
        self.assertEqual(mock_send_email.call_count, 2)
