from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import TicketViewSet, CategoryViewSet, predict_ticket_api, ticket_stats

router = DefaultRouter()
router.register(r'tickets', TicketViewSet)
router.register(r'categories', CategoryViewSet)

urlpatterns = [
    path('', include(router.urls)),
    path('predict/', predict_ticket_api),
    path('stats/', ticket_stats),
    # Support frontend convention from /api/tickets/stats/
    path('tickets/stats/', ticket_stats),
]