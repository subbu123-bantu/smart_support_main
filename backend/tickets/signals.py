from django.db.models.signals import pre_save
from django.dispatch import receiver
from .models import Ticket

@receiver(pre_save, sender=Ticket)
def set_user_ticket_id(sender, instance, **kwargs):

    # 🚨 FIX: check if customer exists
    if not instance.customer_id:
        return

    last_ticket = Ticket.objects.filter(
        customer=instance.customer
    ).order_by('-user_ticket_id').first()

    if last_ticket:
        instance.user_ticket_id = last_ticket.user_ticket_id + 1
    else:
        instance.user_ticket_id = 1