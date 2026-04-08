from django.db import models
from django.conf import settings

from users.models import User


class Category(models.Model):
    name = models.CharField(max_length=100, unique=True)

    def __str__(self):
        return self.name

class Ticket(models.Model):
    title = models.CharField(max_length=255)
    description = models.TextField()

    user_ticket_id = models.PositiveIntegerField(null=True, blank=True)
    assigned_team = models.CharField(max_length=100, blank=True)

    class Status(models.TextChoices):
        OPEN = "open"
        IN_PROGRESS = "in_progress"
        CLOSED = "closed"

    status = models.CharField(max_length=20, choices=Status.choices, default=Status.OPEN)

    category = models.ForeignKey("Category", on_delete=models.SET_NULL, null=True)

    class Priority(models.TextChoices):
        LOW = "low"
        MEDIUM = "medium"
        HIGH = "high"
        URGENT = "urgent"

    priority = models.CharField(max_length=10, choices=Priority.choices, default=Priority.LOW)

    customer = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="tickets"
    )

    assigned_to = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="assigned_tickets"
    )
    predicted_category = models.CharField(max_length=20, null=True, blank=True)
    predicted_priority = models.CharField(max_length=10, null=True, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return self.title
    

class TicketComment(models.Model):
    ticket = models.ForeignKey(Ticket, on_delete=models.CASCADE, related_name="comments")
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    message = models.TextField()
    is_internal = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user.username} - {self.ticket.id}"
    
class TicketPredictionLog(models.Model):
    ticket = models.ForeignKey(Ticket, on_delete=models.CASCADE, null=True, blank=True)

    text = models.TextField()

    predicted_category = models.CharField(max_length=50,blank=True)
    predicted_priority = models.CharField(max_length=20,blank=True)

    source = models.CharField(max_length=20)  # rule / AI / fallback
    confidence = models.FloatField(default=0)
    

    final_accepted = models.BooleanField(null=True, blank=True)  # later used for feedback loop

    created_at = models.DateTimeField(auto_now_add=True)
    
