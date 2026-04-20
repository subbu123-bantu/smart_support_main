from unittest.mock import patch

from django.test import TestCase
from django.utils.crypto import get_random_string
from rest_framework import status
from rest_framework.test import APITestCase

from tickets.models import Category, Ticket, TicketComment, TicketPredictionLog
from tickets.services.assignment import assign_ticket_to_agent, auto_assign_ticket
from tickets.services.ticketcomments import create_comment_for_user, get_comment_queryset_for_user
from tickets.services.ticket_prediction_update import get_prediction_feedback, update_prediction_feedback
from tickets.services.ticketcreate import create_ticket
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
