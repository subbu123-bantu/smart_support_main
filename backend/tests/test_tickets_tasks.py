from unittest.mock import patch

from django.test import TestCase

from tickets.models import Category, Ticket, TicketPredictionLog
from tickets.tasks import run_ai_fallback_prediction_task
from users.models import User

from .test_utils import PASSWORD_FIELD, build_test_password


class TicketTasksTests(TestCase):
    def setUp(self):
        self.customer = User.objects.create_user(
            username="task-customer",
            email="task-customer@example.com",
            **{PASSWORD_FIELD: build_test_password()},
            role="customer",
        )
        self.other_category = Category.objects.create(name="other")
        self.ticket = Ticket.objects.create(
            title="Slow AI ticket",
            description="Need richer prediction",
            customer=self.customer,
            category=self.other_category,
            priority=Ticket.Priority.LOW,
            predicted_category="other",
            predicted_priority=Ticket.Priority.LOW,
            user_ticket_id=1,
        )

    @patch("tickets.tasks.log_prediction")
    @patch("tickets.tasks.predict_ticket")
    @patch("tickets.services.assignment.auto_assign_ticket")
    def test_run_ai_fallback_prediction_task_updates_ticket_and_assigns(
        self,
        mock_auto_assign,
        mock_predict_ticket,
        mock_log_prediction,
    ):
        mock_predict_ticket.return_value = {
            "category": "network",
            "priority": Ticket.Priority.HIGH,
            "confidence": 0.91,
            "source": "ai",
            "needs_manual_review": False,
        }

        run_ai_fallback_prediction_task.run(self.ticket.id, "router is down")

        self.ticket.refresh_from_db()
        self.assertEqual(self.ticket.predicted_category, "network")
        self.assertEqual(self.ticket.predicted_priority, Ticket.Priority.HIGH)
        self.assertEqual(self.ticket.category.name, "network")
        self.assertEqual(self.ticket.priority, Ticket.Priority.HIGH)
        mock_log_prediction.assert_called_once_with(
            "router is down",
            mock_predict_ticket.return_value,
            self.ticket,
        )
        mock_auto_assign.assert_called_once_with(self.ticket)

    @patch("tickets.tasks.log_prediction")
    @patch("tickets.tasks.predict_ticket", side_effect=RuntimeError("ai unavailable"))
    def test_run_ai_fallback_prediction_task_retries_on_failure(
        self,
        mock_predict_ticket,
        mock_log_prediction,
    ):
        with self.assertRaises(RuntimeError):
            run_ai_fallback_prediction_task.run(self.ticket.id, "router is down")

        mock_predict_ticket.assert_called_once_with("router is down")
        mock_log_prediction.assert_not_called()
        self.ticket.refresh_from_db()
        self.assertEqual(self.ticket.predicted_category, "other")
        self.assertEqual(TicketPredictionLog.objects.count(), 0)
