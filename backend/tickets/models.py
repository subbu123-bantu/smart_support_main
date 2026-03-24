from django.db import models
from django.conf import settings

# Create your models here.

class Category(models.Model):
    name=models.CharField(max_length=100)
    description=models.TextField(blank=True)

    def __str__(self):
        return self.name
    
class Ticket(models.Model):
    title = models.CharField(max_length=255)
    description = models.TextField()

    user_ticket_id = models.PositiveIntegerField(editable=False, blank=True, null=True)

    STATUS_CHOICES = [
        ("open", "Open"),
        ("in_progress", "In Progress"),
        ("closed", "Closed"),
    ]
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="open")

    CATEGORY_CHOICES = [
        ("technical", "Technical"),
        ("billing", "Billing"),
        ("authentication", "Authentication"),
        ("network", "Network"),
        ("account", "Account"),
        ("other", "Other"),
    ]
    category = models.CharField(max_length=20, choices=CATEGORY_CHOICES, default="other")

    PRIORITY_CHOICES = [
        ("low", "Low"),
        ("medium", "Medium"),
        ("high", "High"),
        ("urgent", "Urgent"),
    ]
    priority = models.CharField(max_length=10, choices=PRIORITY_CHOICES, default="low")

    customer = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='tickets'
    )

    #AI fields
    predicted_category = models.CharField(max_length=20, null=True, blank=True)
    predicted_priority = models.CharField(max_length=10, null=True, blank=True)
    auto_assigned = models.BooleanField(default=False)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]

    def save(self, *args, **kwargs):
        if not self.user_ticket_id:
            last_ticket = Ticket.objects.filter(customer=self.customer).order_by('-user_ticket_id').first()
            self.user_ticket_id = 1 if not last_ticket else last_ticket.user_ticket_id + 1
        super().save(*args, **kwargs)

    def __str__(self):
        return self.title
