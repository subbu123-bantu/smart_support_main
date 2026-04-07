from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import TicketViewSet, CategoryViewSet
from .views import ticket_stats,assign_ticket
router = DefaultRouter()
router.register(r'tickets', TicketViewSet,basename='ticket')
router.register(r'categories', CategoryViewSet,basename='category')

urlpatterns = [
    path('', include(router.urls)),
    path('stats/', ticket_stats),   
    path('tickets/<int:ticket_id>/assign/', assign_ticket),    
]