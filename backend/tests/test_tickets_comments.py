from unittest.mock import patch

from django.test import TestCase
from rest_framework.exceptions import PermissionDenied

from tickets.models import Category, Ticket, TicketComment
from tickets.services.ticketcomments import (
    can_delete_comment,
    create_comment_for_user,
    get_comment_queryset_for_user,
    get_ticket_or_raise,
)
from users.models import User

from .test_utils import PASSWORD_FIELD, build_test_password


class TicketCommentServiceTests(TestCase):
    def setUp(self):
        self.admin_user = User.objects.create_user(
            username="admincomments",
            email="admincomments@example.com",
            **{PASSWORD_FIELD: build_test_password()},
            role="admin",
        )
        self.agent_user = User.objects.create_user(
            username="agentcomments",
            email="agentcomments@example.com",
            **{PASSWORD_FIELD: build_test_password()},
            role="agent",
        )
        self.customer_user = User.objects.create_user(
            username="customercomments",
            email="customercomments@example.com",
            **{PASSWORD_FIELD: build_test_password()},
            role="customer",
        )
        self.other_customer = User.objects.create_user(
            username="othercomments",
            email="othercomments@example.com",
            **{PASSWORD_FIELD: build_test_password()},
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
