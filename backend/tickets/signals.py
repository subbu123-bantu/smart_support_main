from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import Ticket
from .services.assignment import assign_ticket  # your function

@receiver(post_save, sender=Ticket)
def auto_assign_ticket(sender, instance, created, **kwargs):
    # Only assign when ticket is created
    if created and not instance.assigned_to:
        agent = assign_ticket(instance)

        if agent:
            instance.assigned_to = agent
            instance.save(update_fields=["assigned_to"])