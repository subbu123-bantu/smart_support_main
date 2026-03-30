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
    
    assigned_team = models.CharField(max_length=100, blank=True)
    embedding = models.JSONField(null=True, blank=True) 

    STATUS_CHOICES = [
        ("open", "Open"),
        ("in_progress", "In Progress"),
        ("closed", "Closed"),
    ]
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="open")

    CATEGORY_CHOICES=[
        ("Low","low"),
        ("Medium","Medium"),
        ("High","high"),
    ]
    PRIORITY_CHOICES = [
        ("low", "Low"),
        ("medium", "Medium"),
        ("high", "High"),
    ]
    customer = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='tickets'
    )
    category = models.ForeignKey(
        Category,
        on_delete=models.SET_NULL,
        null=True
    )

    priority = models.CharField(max_length=10, choices=PRIORITY_CHOICES, default="low")

    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.title
    
class TicketPredictionLog(models.Model):
    text = models.TextField()

    predicted_category = models.CharField(max_length=50)
    predicted_priority = models.CharField(max_length=20)

    source = models.CharField(max_length=20)  # rule / AI / fallback
    confidence = models.FloatField(default=0)

    final_accepted = models.BooleanField(default=True)  # later used for feedback loop

    created_at = models.DateTimeField(auto_now_add=True)
