from tickets.views import TicketViewSet, CategoryViewSet
from rest_framework.routers import DefaultRouter
from .views import ticket_stats
from django.urls import path

router = DefaultRouter()
router.register(r'tickets', TicketViewSet,basename='ticket')
router.register(r'categories', CategoryViewSet)

urlpatterns = [
    path('tickets/stats/', ticket_stats),  # ✅ plain path, not router.register
]
urlpatterns+=router.urls