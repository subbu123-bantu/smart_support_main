from django.db import models
from django.conf import settings

# Create your models here.

class Category(models.Model):
    name=models.CharField(max_length=100)
    description=models.TextField(blank=True)

    def __str__(self):
        return self.name
    
class TicketStatus(models.Model):
    name=models.CharField(max_length=20)

    def __str__(self):
        return self.name
    
class Ticket(models.Model):
    title = models.CharField(max_length=255)
    description = models.TextField()

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

    status = models.ForeignKey(
        TicketStatus,
        on_delete=models.SET_NULL,
        null=True
    )

    priority = models.CharField(max_length=20, default="low")

    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.title