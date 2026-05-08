import logging

from django.conf import settings
from django.db import transaction
from rest_framework.exceptions import PermissionDenied

from tickets.models import Ticket, TicketComment
from tickets.tasks import send_email_task

logger = logging.getLogger(__name__)


class TicketCommentService:
    def get_ticket_or_raise(self, ticket_id):
        try:
            return Ticket.objects.get(id=ticket_id)
        except Ticket.DoesNotExist:
            raise PermissionDenied("Ticket not found.")

    def _role(self, user):
        return user.role.lower()

    def _notify_customer(self, ticket, user, comment, role):
        try:
            send_email_task.delay(
                ticket.customer.email,
                subject=f"[Ticket #{ticket.id}] New comment on your ticket",
                template_name="emails/ticket_comment_added.html",
                context={
                    "customer_name": ticket.customer.username,
                    "ticket_title": ticket.title,
                    "ticket_id": ticket.id,
                    "ticket_url": f"{settings.FRONTEND_URL.rstrip('/')}/tickets/{ticket.id}",
                    "comment_by": user.username,
                    "comment_message": comment.message[:300],
                    "comment_role": role,
                }
            )
        except Exception:
            logger.exception(
                "Failed to queue comment email for ticket_id=%s comment_id=%s",
                ticket.id,
                comment.id,
            )

    def get_comment_queryset_for_user(self, user, ticket):
        role = self._role(user)
        match role:
      
            case "admin":
                queryset = TicketComment.objects.filter(ticket=ticket)
        
            case "agent":
                if ticket.assigned_to != user:
                    raise PermissionDenied("You can only view comments on your assigned tickets.")
                queryset = TicketComment.objects.filter(ticket=ticket)
        
            case "customer":
                if ticket.customer != user:
                    raise PermissionDenied("You can only view comments on your own tickets.")
                queryset = TicketComment.objects.filter(ticket=ticket, is_internal=False)
            case _:
                raise PermissionDenied("Invalid role.")

        return queryset.select_related("user", "ticket").order_by("created_at")

    def create_comment_for_user(self, serializer, user, ticket):
        role =self._role(user)
        match role:
            case "admin":
                comment = serializer.save(ticket=ticket, user=user)
            case "agent":
                if ticket.assigned_to != user:
                    raise PermissionDenied("You can only comment on your assigned tickets.")
                comment = serializer.save(ticket=ticket, user=user)
            case "customer":
                if ticket.customer != user:
                    raise PermissionDenied("You can only comment on your own tickets.")
                comment = serializer.save(ticket=ticket, user=user, is_internal=False)
            case _:
                raise PermissionDenied("Invalid role.")

        if role in ["admin", "agent"] and not comment.is_internal:
            transaction.on_commit(
                lambda: self._notify_customer(ticket, user, comment, role)
            )

        return comment

    def can_delete_comment(self, user, comment):
        role = self._role(user)

        match role:
            case "admin":
                return True

        if comment.user != user:
            raise PermissionDenied("You can only delete your own comments.")


COMMENT_SERVICE = TicketCommentService()


def get_ticket_or_raise(ticket_id):
    return COMMENT_SERVICE.get_ticket_or_raise(ticket_id)


def get_comment_queryset_for_user(user, ticket):
    return COMMENT_SERVICE.get_comment_queryset_for_user(user, ticket)


def create_comment_for_user(serializer, user, ticket):
    return COMMENT_SERVICE.create_comment_for_user(serializer, user, ticket)


def can_delete_comment(user, comment):
    return COMMENT_SERVICE.can_delete_comment(user, comment)
