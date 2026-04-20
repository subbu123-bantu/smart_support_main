from types import SimpleNamespace
from unittest.mock import Mock, patch

from django.test import TestCase
from django.utils.crypto import get_random_string
from rest_framework.exceptions import PermissionDenied
from rest_framework import status
from rest_framework.test import APITestCase

from tickets.ai.ai import (
    best_keyword_category,
    choose_final,
    log_prediction,
    needs_manual_review,
    predict_ticket,
    resolve_low_confidence,
    rule_engine,
)
from tickets.ai.ai_client import ai_classification, build_groq_payload, call_groq, parse_ai_result
from tickets.ai.ai_helper import count_generic_only, is_generic_input, is_weak_input, phrase_score, preprocess
from tickets.ai.ai_overrides import apply_conflict_overrides, apply_override, starts_with_refund_request
from tickets.ai.ai_priority import get_priority
from tickets.exceptions import EmailSendError
from tickets.models import Category, Ticket, TicketComment, TicketPredictionLog
from requests import RequestException
from tickets.services.assignment import assign_ticket_to_agent, auto_assign_ticket
from tickets.services.ticketcomments import (
    can_delete_comment,
    create_comment_for_user,
    get_comment_queryset_for_user,
    get_ticket_or_raise,
)
from tickets.services.ticket_prediction_update import get_prediction_feedback, update_prediction_feedback
from tickets.services.ticketcreate import create_ticket
from tickets.tasks import send_email_task
from users.models import AgentProfile, User


PASSWORD_FIELD = "password"


def build_test_password():
    return f"test-{get_random_string(16)}-Aa1!"


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
        self.admin_password = build_test_password()
        self.agent_password = build_test_password()
        self.customer_password = build_test_password()
        self.other_customer_password = build_test_password()

        self.admin_user = User.objects.create_user(
            username="admincomments",
            email="admincomments@example.com",
            **{PASSWORD_FIELD: self.admin_password},
            role="admin",
        )
        self.agent_user = User.objects.create_user(
            username="agentcomments",
            email="agentcomments@example.com",
            **{PASSWORD_FIELD: self.agent_password},
            role="agent",
        )
        self.customer_user = User.objects.create_user(
            username="customercomments",
            email="customercomments@example.com",
            **{PASSWORD_FIELD: self.customer_password},
            role="customer",
        )
        self.other_customer = User.objects.create_user(
            username="othercomments",
            email="othercomments@example.com",
            **{PASSWORD_FIELD: self.other_customer_password},
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

    def test_get_ticket_or_raise_returns_ticket_for_existing_id(self):
        self.assertEqual(get_ticket_or_raise(self.ticket.id), self.ticket)

    def test_get_ticket_or_raise_denies_missing_ticket(self):
        with self.assertRaisesMessage(PermissionDenied, "Ticket not found."):
            get_ticket_or_raise(999999)

    def test_get_comment_queryset_for_admin_returns_all_comments(self):
        queryset = get_comment_queryset_for_user(self.admin_user, self.ticket)

        self.assertEqual(list(queryset), [self.public_comment, self.internal_comment])

    def test_get_comment_queryset_for_assigned_agent_returns_all_ticket_comments(self):
        queryset = get_comment_queryset_for_user(self.agent_user, self.ticket)

        self.assertEqual(list(queryset), [self.public_comment, self.internal_comment])

    def test_get_comment_queryset_for_unassigned_agent_denies_access(self):
        other_agent = User.objects.create_user(
            username="outsider-agent",
            email="outsider-agent@example.com",
            **{PASSWORD_FIELD: build_test_password()},
            role="agent",
        )

        with self.assertRaisesMessage(PermissionDenied, "You can only view comments on your assigned tickets."):
            get_comment_queryset_for_user(other_agent, self.ticket)

    def test_get_comment_queryset_for_wrong_customer_denies_access(self):
        with self.assertRaisesMessage(PermissionDenied, "You can only view comments on your own tickets."):
            get_comment_queryset_for_user(self.other_customer, self.ticket)

    def test_get_comment_queryset_rejects_invalid_role(self):
        outsider = User.objects.create_user(
            username="invalid-role-user",
            email="invalid-role@example.com",
            **{PASSWORD_FIELD: build_test_password()},
            role="admin",
        )
        outsider.role = "manager"

        with self.assertRaisesMessage(PermissionDenied, "Invalid role."):
            get_comment_queryset_for_user(outsider, self.ticket)

    @patch("tickets.services.ticketcomments.send_email_task.delay")
    def test_create_comment_for_customer_forces_non_internal(self, mock_delay):
        class DummySerializer:
            def save(self, **kwargs):
                return TicketComment.objects.create(message="Customer reply", **kwargs)

        comment = create_comment_for_user(DummySerializer(), self.customer_user, self.ticket)

        self.assertFalse(comment.is_internal)
        mock_delay.assert_not_called()

    @patch("tickets.services.ticketcomments.send_email_task.delay", side_effect=Exception("broker unavailable"))
    def test_create_comment_for_agent_succeeds_when_email_queue_fails(self, mock_delay):
        class DummySerializer:
            def save(self, **kwargs):
                return TicketComment.objects.create(message="Agent reply", **kwargs)

        comment = create_comment_for_user(DummySerializer(), self.agent_user, self.ticket)

        self.assertEqual(comment.message, "Agent reply")
        mock_delay.assert_called_once()

    @patch("tickets.services.ticketcomments.send_email_task.delay")
    def test_create_comment_for_admin_allows_internal_comment_without_email(self, mock_delay):
        class DummySerializer:
            def save(self, **kwargs):
                return TicketComment.objects.create(message="Internal admin note", is_internal=True, **kwargs)

        comment = create_comment_for_user(DummySerializer(), self.admin_user, self.ticket)

        self.assertTrue(comment.is_internal)
        mock_delay.assert_not_called()

    def test_create_comment_for_unassigned_agent_denies_access(self):
        outsider = User.objects.create_user(
            username="comment-outsider-agent",
            email="comment-outsider-agent@example.com",
            **{PASSWORD_FIELD: build_test_password()},
            role="agent",
        )

        class DummySerializer:
            def save(self, **kwargs):
                return TicketComment.objects.create(message="Should not save", **kwargs)

        with self.assertRaisesMessage(PermissionDenied, "You can only comment on your assigned tickets."):
            create_comment_for_user(DummySerializer(), outsider, self.ticket)

    def test_create_comment_for_wrong_customer_denies_access(self):
        class DummySerializer:
            def save(self, **kwargs):
                return TicketComment.objects.create(message="Should not save", **kwargs)

        with self.assertRaisesMessage(PermissionDenied, "You can only comment on your own tickets."):
            create_comment_for_user(DummySerializer(), self.other_customer, self.ticket)

    def test_create_comment_rejects_invalid_role(self):
        outsider = User.objects.create_user(
            username="comment-invalid-role",
            email="comment-invalid-role@example.com",
            **{PASSWORD_FIELD: build_test_password()},
            role="admin",
        )
        outsider.role = "manager"

        class DummySerializer:
            def save(self, **kwargs):
                return TicketComment.objects.create(message="Should not save", **kwargs)

        with self.assertRaisesMessage(PermissionDenied, "Invalid role."):
            create_comment_for_user(DummySerializer(), outsider, self.ticket)

    def test_can_delete_comment_returns_true_for_admin(self):
        self.assertTrue(can_delete_comment(self.admin_user, self.public_comment))

    def test_can_delete_comment_denies_other_users(self):
        with self.assertRaisesMessage(PermissionDenied, "You can only delete your own comments."):
            can_delete_comment(self.customer_user, self.public_comment)


class TicketAssignmentServiceTests(TestCase):
    def setUp(self):
        self.customer_password = build_test_password()
        self.agent_one_password = build_test_password()
        self.agent_two_password = build_test_password()

        self.customer = User.objects.create_user(
            username="svc-customer",
            email="svc-customer@example.com",
            **{PASSWORD_FIELD: self.customer_password},
            role="customer",
        )
        self.agent_one = User.objects.create_user(
            username="svc-agent-one",
            email="svc-agent-one@example.com",
            **{PASSWORD_FIELD: self.agent_one_password},
            role="agent",
        )
        self.agent_two = User.objects.create_user(
            username="svc-agent-two",
            email="svc-agent-two@example.com",
            **{PASSWORD_FIELD: self.agent_two_password},
            role="agent",
        )

        self.network = Category.objects.create(name="network")
        self.billing = Category.objects.create(name="billing")

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


class TicketPredictionFeedbackServiceTests(TestCase):
    def setUp(self):
        self.customer_password = build_test_password()
        self.agent_password = build_test_password()
        self.other_agent_password = build_test_password()

        self.customer = User.objects.create_user(
            username="feedback-customer",
            email="feedback-customer@example.com",
            **{PASSWORD_FIELD: self.customer_password},
            role="customer",
        )
        self.agent = User.objects.create_user(
            username="feedback-agent",
            email="feedback-agent@example.com",
            **{PASSWORD_FIELD: self.agent_password},
            role="agent",
        )
        self.other_agent = User.objects.create_user(
            username="feedback-other-agent",
            email="feedback-other-agent@example.com",
            **{PASSWORD_FIELD: self.other_agent_password},
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


class TicketCreateServiceTests(TestCase):
    def setUp(self):
        self.customer_password = build_test_password()
        self.agent_password = build_test_password()

        self.customer = User.objects.create_user(
            username="create-customer",
            email="create-customer@example.com",
            **{PASSWORD_FIELD: self.customer_password},
            role="customer",
        )
        self.agent = User.objects.create_user(
            username="create-agent",
            email="create-agent@example.com",
            **{PASSWORD_FIELD: self.agent_password},
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

        ticket = create_ticket(
            {"title": "Router issue", "description": "Router is down"},
            self.customer,
        )

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

        ticket = create_ticket(
            {"title": "Billing issue", "description": "Need invoice help"},
            self.customer,
        )

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

        first_ticket = create_ticket(
            {"title": "First issue", "description": "First description"},
            self.customer,
        )
        second_ticket = create_ticket(
            {"title": "Second issue", "description": "Second description"},
            self.customer,
        )

        self.assertEqual(first_ticket.user_ticket_id, 1)
        self.assertEqual(second_ticket.user_ticket_id, 2)
        self.assertEqual(mock_log_prediction.call_count, 2)
        self.assertEqual(mock_send_email.call_count, 2)


class TicketAiHelpersTests(TestCase):
    def test_preprocess_normalizes_whitespace_and_punctuation(self):
        self.assertEqual(preprocess("  Server ERROR!!! \n "), "server error")

    def test_phrase_score_counts_single_and_multi_word_matches(self):
        score, matches = phrase_score("payment failed and refund pending", ["payment", "payment failed", "refund"])

        self.assertEqual(score, 5)
        self.assertEqual(matches, ["payment", "payment failed", "refund"])

    def test_generic_and_weak_input_helpers_cover_edge_cases(self):
        self.assertTrue(count_generic_only([]))
        self.assertTrue(is_weak_input(["help"], "help"))
        self.assertTrue(is_generic_input(["issue", "problem"], "issue problem"))
        self.assertFalse(is_generic_input(["invoice", "refund"], "invoice refund"))


class TicketAiOverrideAndPriorityTests(TestCase):
    def test_apply_override_updates_category_source_and_confidence(self):
        final = {"category": "other", "source": "fallback", "confidence": 0.2}

        apply_override(final, "billing", "billing_override", 0.88)

        self.assertEqual(final, {"category": "billing", "source": "billing_override", "confidence": 0.88})

    def test_starts_with_refund_request_detects_refund_prefixes(self):
        self.assertTrue(starts_with_refund_request(" refund was charged twice"))
        self.assertTrue(starts_with_refund_request("need refund immediately"))
        self.assertFalse(starts_with_refund_request("please help with refund"))

    def test_apply_conflict_overrides_shifts_to_billing_for_refund_wording(self):
        final = {"category": "technical", "source": "rule", "confidence": 0.72}

        updated = apply_conflict_overrides("refund request because app crash charged twice", final)

        self.assertEqual(updated["category"], "billing")
        self.assertEqual(updated["source"], "billing_override")

    def test_apply_conflict_overrides_shifts_to_authentication_when_verification_link_present(self):
        final = {"category": "account", "source": "rule", "confidence": 0.70}

        updated = apply_conflict_overrides("verification link is invalid and login fails", final)

        self.assertEqual(updated["category"], "authentication")
        self.assertEqual(updated["source"], "auth_override")

    def test_get_priority_covers_urgent_category_specific_and_default_paths(self):
        self.assertEqual(get_priority("production down for all users", "technical"), "urgent")
        self.assertEqual(get_priority("payment failed and charged twice", "billing"), "high")
        self.assertEqual(get_priority("cannot connect to dashboard after login", "network"), "medium")
        self.assertEqual(get_priority("password reset verification link expired", "authentication"), "medium")
        self.assertEqual(get_priority("update profile display name", "account"), "low")
        self.assertEqual(get_priority("error happened but user can still continue", None), "low")


class TicketAiClientTests(TestCase):
    def test_build_groq_payload_uses_expected_model_and_prompt_shape(self):
        payload = build_groq_payload("Classify this ticket")

        self.assertIn("model", payload)
        self.assertEqual(payload["messages"][1]["content"], "Classify this ticket")
        self.assertEqual(payload["temperature"], 0.1)

    @patch("tickets.ai.ai_client.GROQ_API_KEY", None)
    def test_call_groq_returns_none_without_api_key(self):
        self.assertIsNone(call_groq("ticket text"))

    @patch("tickets.ai.ai_client.requests.post")
    @patch("tickets.ai.ai_client.GROQ_API_KEY", "token")
    def test_call_groq_returns_message_content_on_success(self, mock_post):
        mock_response = Mock()
        mock_response.json.return_value = {"choices": [{"message": {"content": '{"category":"billing","confidence":0.81}'}}]}
        mock_response.raise_for_status.return_value = None
        mock_post.return_value = mock_response

        result = call_groq("ticket text")

        self.assertEqual(result, '{"category":"billing","confidence":0.81}')

    @patch("tickets.ai.ai_client.requests.post", side_effect=RequestException("network down"))
    @patch("tickets.ai.ai_client.GROQ_API_KEY", "token")
    def test_call_groq_returns_none_on_request_failure(self, _mock_post):
        self.assertIsNone(call_groq("ticket text"))

    def test_parse_ai_result_accepts_json_and_clamps_confidence(self):
        parsed = parse_ai_result('{"category":"technical","confidence":0.99}')

        self.assertEqual(parsed["category"], "technical")
        self.assertEqual(parsed["confidence"], 0.88)
        self.assertEqual(parsed["source"], "AI")

    def test_parse_ai_result_returns_none_for_invalid_payload(self):
        self.assertIsNone(parse_ai_result("not-json"))

    @patch("tickets.ai.ai_client.call_groq")
    def test_ai_classification_uses_call_and_parse_pipeline(self, mock_call_groq):
        mock_call_groq.return_value = '{"category":"network","confidence":0.67}'

        result = ai_classification("router timeout")

        self.assertEqual(result["category"], "network")
        self.assertEqual(result["source"], "AI")


class TicketAiDecisionTests(TestCase):
    def test_rule_engine_returns_short_input_fallback(self):
        result = rule_engine("help")

        self.assertEqual(result["category"], "other")
        self.assertEqual(result["source"], "rule_short_input")

    def test_rule_engine_scores_billing_keywords(self):
        result = rule_engine("payment failed and refund deducted twice")

        self.assertEqual(result["category"], "billing")
        self.assertEqual(result["source"], "rule")
        self.assertGreater(result["confidence"], 0.78)

    def test_best_keyword_category_returns_none_without_matches(self):
        self.assertIsNone(best_keyword_category("completely unrelated wording"))

    def test_choose_final_prefers_agreeing_rule_and_ai(self):
        result = choose_final(
            {"category": "billing", "confidence": 0.8, "source": "rule"},
            {"category": "billing", "confidence": 0.82, "source": "AI"},
            None,
        )

        self.assertEqual(result, {"category": "billing", "confidence": 0.86, "source": "rule+AI"})

    def test_choose_final_prefers_highest_confidence_when_sources_disagree(self):
        result = choose_final(
            {"category": "billing", "confidence": 0.8, "source": "rule"},
            {"category": "technical", "confidence": 0.84, "source": "AI"},
            {"category": "network", "confidence": 0.7, "source": "keyword_fallback"},
        )

        self.assertEqual(result["category"], "technical")

    def test_resolve_low_confidence_uses_soft_fallback_and_threshold_reject(self):
        final = {"source": "rule"}
        category, confidence = resolve_low_confidence("billing", 0.6, final, {"category": "technical", "confidence": 0.71, "matches": ["server error", "dashboard"]})
        self.assertEqual((category, confidence, final["source"]), ("technical", 0.72, "soft_fallback"))

        final = {"source": "rule"}
        category, confidence = resolve_low_confidence("billing", 0.6, final, {"category": "technical", "confidence": 0.71, "matches": ["server error"]})
        self.assertEqual((category, confidence, final["source"]), ("other", 0.48, "threshold_reject"))

    def test_needs_manual_review_flags_low_confidence_and_fallback_sources(self):
        self.assertTrue(needs_manual_review("other", 0.9, "rule"))
        self.assertTrue(needs_manual_review("billing", 0.8, "rule"))
        self.assertTrue(needs_manual_review("billing", 0.9, "soft_fallback"))
        self.assertFalse(needs_manual_review("billing", 0.9, "rule"))

    @patch("tickets.ai.ai.ai_classification")
    def test_predict_ticket_rejects_weak_and_generic_inputs_before_ai(self, mock_ai_classification):
        weak = predict_ticket("help")
        generic = predict_ticket("help issue problem update")

        self.assertEqual(weak["source"], "weak_input_reject")
        self.assertEqual(generic["source"], "generic_input_reject")
        mock_ai_classification.assert_not_called()

    @patch("tickets.ai.ai.apply_conflict_overrides")
    @patch("tickets.ai.ai.ai_classification")
    def test_predict_ticket_handles_invalid_final_category_and_returns_priority(self, mock_ai_classification, mock_apply_conflict_overrides):
        mock_ai_classification.return_value = {"category": "technical", "confidence": 0.84, "source": "AI"}
        mock_apply_conflict_overrides.return_value = {"category": "unknown", "confidence": 0.9, "source": "weird"}

        result = predict_ticket("dashboard crashes with server error")

        self.assertEqual(result["category"], "other")
        self.assertEqual(result["source"], "fallback")
        self.assertEqual(result["priority"], "low")
        self.assertTrue(result["needs_manual_review"])

    @patch("tickets.ai.ai.ai_classification")
    def test_predict_ticket_returns_resolved_category_for_real_input(self, mock_ai_classification):
        mock_ai_classification.return_value = {"category": "billing", "confidence": 0.86, "source": "AI"}

        result = predict_ticket("payment failed and invoice page not loading")

        self.assertEqual(result["category"], "billing")
        self.assertIn(result["source"], {"rule+AI", "billing_override", "soft_fallback", "rule"})
        self.assertIn(result["priority"], {"high", "medium", "urgent", "low"})

    def test_log_prediction_creates_prediction_log_record(self):
        ticket = Ticket.objects.create(
            title="Logged prediction",
            description="Track this prediction",
            category=Category.objects.create(name="logged"),
            priority=Ticket.Priority.LOW,
            customer=User.objects.create_user(
                username="logger-customer",
                email="logger-customer@example.com",
                **{PASSWORD_FIELD: build_test_password()},
                role="customer",
            ),
            user_ticket_id=1,
        )

        log_prediction("ticket text", {"category": "billing", "priority": "high", "source": "rule", "confidence": 0.77}, ticket)

        log = TicketPredictionLog.objects.get(ticket=ticket)
        self.assertEqual(log.predicted_category, "billing")
        self.assertEqual(log.predicted_priority, "high")


class TicketTaskAndExceptionTests(TestCase):
    def test_email_send_error_formats_status_and_message(self):
        error = EmailSendError(status_code=400, message="Bad request")

        self.assertEqual(str(error), "[400] Bad request")
        self.assertEqual(error.status_code, 400)

    @patch("tickets.tasks.logger")
    @patch("tickets.tasks.requests.post")
    @patch("tickets.tasks.render_to_string", return_value="<p>Hello</p>")
    def test_send_email_task_logs_success_for_200_responses(self, _mock_render, mock_post, mock_logger):
        mock_post.return_value = SimpleNamespace(status_code=201, text="created")

        send_email_task.run("user@example.com", "Subject", context={"name": "User"})

        mock_post.assert_called_once()
        mock_logger.info.assert_called_once()

    @patch("tickets.tasks.logger")
    @patch("tickets.tasks.requests.post")
    @patch("tickets.tasks.render_to_string", return_value="<p>Hello</p>")
    @patch.object(send_email_task, "retry", side_effect=RuntimeError("retry called"))
    def test_send_email_task_retries_when_brevo_returns_error(self, mock_retry, _mock_render, mock_post, mock_logger):
        mock_post.return_value = SimpleNamespace(status_code=500, text="server error")

        with self.assertRaisesMessage(RuntimeError, "retry called"):
            send_email_task.run("user@example.com", "Subject")

        mock_logger.error.assert_called_once()
        mock_retry.assert_called_once()
