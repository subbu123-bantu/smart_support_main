from django.contrib.auth.models import AbstractUser
from django.db import models
from django.conf import settings

class User(AbstractUser):
    ROLE_CHOICES = (
        ('admin', 'Admin'),
        ('agent', 'Agent'),
        ('customer', 'Customer'),
    )

    role = models.CharField(max_length=10, choices=ROLE_CHOICES)
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return f"{self.username} ({self.get_role_display()})"
    
class AgentProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    categories = models.ManyToManyField("tickets.Category")
    is_available = models.BooleanField(default=True)

    def __str__(self):
        return self.user.username