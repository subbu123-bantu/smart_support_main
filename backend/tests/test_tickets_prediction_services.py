from django.test import TestCase

from tickets.models import Category, Ticket, TicketPredictionLog
from tickets.services.ticket_prediction_update import get_prediction_feedback, update_prediction_feedback
from users.models import User

from .test_utils import PASSWORD_FIELD, build_test_password


class TicketPredictionFeedbackServiceTests(TestCase):
    def setUp(self):
        self.customer = User.objects.create_user(
            username="feedback-customer",
            email="feedback-customer@example.com",
            **{PASSWORD_FIELD: build_test_password()},
            role="customer",
        )
        self.agent = User.objects.create_user(
            username="feedback-agent",
            email="feedback-agent@example.com",
            **{PASSWORD_FIELD: build_test_password()},
            role="agent",
        )
        self.other_agent = User.objects.create_user(
            username="feedback-other-agent",
            email="feedback-other-agent@example.com",
            **{PASSWORD_FIELD: build_test_password()},
            role="agent",
        )
        self.category = Category.objects.create(name="Hardware")
        self.ticket = Ticket.objects.create(
            title="Prediction feedback ticket",
            description="Track feedback",
            category=self.category,
            priority=Ticket.Priority.HIGH,
            customer=self.customer,
            assigned_to=self.agent,
            user_ticket_id=1,
        )

    def test_update_prediction_feedback_returns_without_log(self):
        update_prediction_feedback(self.ticket)
        self.assertEqual(TicketPredictionLog.objects.count(), 0)

    def test_update_prediction_feedback_sets_correctness_flags(self):
        log = TicketPredictionLog.objects.create(
            ticket=self.ticket,
            text="Laptop keeps shutting down",
            predicted_category=" hardware ",
            predicted_priority="HIGH",
            source="ai",
            confidence=0.98,
        )
        update_prediction_feedback(self.ticket)
        log.refresh_from_db()
        self.assertEqual(log.actual_category, "Hardware")
        self.assertEqual(log.actual_priority, Ticket.Priority.HIGH)
        self.assertTrue(log.category_correct)
        self.assertTrue(log.priority_correct)

    def test_update_prediction_feedback_handles_missing_actual_values(self):
        self.ticket.category = None
        self.ticket.priority = ""
        log = TicketPredictionLog.objects.create(
            ticket=self.ticket,
            text="No actual values yet",
            predicted_category="hardware",
            predicted_priority="low",
            source="rules",
            confidence=0.44,
        )
        update_prediction_feedback(self.ticket)
        log.refresh_from_db()
        self.assertIsNone(log.category_correct)
        self.assertIsNone(log.priority_correct)

    def test_get_prediction_feedback_returns_404_for_missing_ticket(self):
        ticket, payload, status_code = get_prediction_feedback(999999, self.customer)
        self.assertIsNone(ticket)
        self.assertEqual(status_code, 404)
        self.assertEqual(payload, {"error": "Ticket not found"})

    def test_get_prediction_feedback_returns_message_when_log_missing(self):
        ticket, payload, status_code = get_prediction_feedback(self.ticket.id, self.customer)
        self.assertEqual(status_code, 200)
        self.assertEqual(ticket, self.ticket)
        self.assertFalse(payload["has_feedback"])
        self.assertIn("No prediction feedback found", payload["message"])

    def test_get_prediction_feedback_blocks_unassigned_agents(self):
        with self.assertRaisesMessage(Exception, "You can only view feedback for your assigned tickets."):
            get_prediction_feedback(self.ticket.id, self.other_agent)

    def test_get_prediction_feedback_returns_latest_log_payload(self):
        TicketPredictionLog.objects.create(
            ticket=self.ticket,
            text="Older prediction",
            predicted_category="billing",
            predicted_priority="low",
            source="rules",
            confidence=0.4,
        )
        latest = TicketPredictionLog.objects.create(
            ticket=self.ticket,
            text="Latest prediction",
            predicted_category="hardware",
            predicted_priority="high",
            source="ai",
            confidence=0.91,
            actual_category="Hardware",
            actual_priority=Ticket.Priority.HIGH,
            category_correct=True,
            priority_correct=True,
        )
        ticket, payload, status_code = get_prediction_feedback(self.ticket.id, self.agent)
        self.assertEqual(status_code, 200)
        self.assertEqual(ticket, self.ticket)
        self.assertTrue(payload["has_feedback"])
        self.assertEqual(payload["predicted_category"], latest.predicted_category)
        self.assertEqual(payload["confidence"], latest.confidence)
        self.assertTrue(payload["category_correct"])
