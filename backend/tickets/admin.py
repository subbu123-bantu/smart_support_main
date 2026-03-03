from django.contrib import admin
from .models import Ticket,Category
# Register your models here.

admin.site.register(Ticket)
admin.site.register(Category)
# class TicketAdmin(admin.ModelAdmin):
#     list_display=('title','customer','assigned_to','priority','status','created_at')
#     list_filter =('status','priority','category')
#     search_fields=('title','description')