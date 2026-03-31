from django.db.models.signals import pre_save
from django.dispatch import receiver
from .models import Ticket

@receiver(pre_save, sender=Ticket)
def set_user_ticket_id(sender, instance, **kwargs):
    if not instance.user_ticket_id:  # Only if not already set
        last_ticket = Ticket.objects.filter(customer=instance.customer).order_by('-user_ticket_id').first()
        instance.user_ticket_id = (last_ticket.user_ticket_id + 1) if last_ticket else 1