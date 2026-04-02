from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import TicketViewSet, CategoryViewSet
from .views import predict_ticket_api, ticket_stats,assign_ticket
router = DefaultRouter()
router.register(r'tickets', TicketViewSet,basename='ticket')
router.register(r'categories', CategoryViewSet,basename='category')

urlpatterns = [
    path('', include(router.urls)),
    path('predict/', predict_ticket_api),
    path('stats/', ticket_stats),   
    path('tickets/<int:ticket_id>/assign/', assign_ticket),    
    # path('update_feedback/', update_prediction_feedback),
    # path('prediction_accuracy/', prediction_accuracy),
    # path('check_assignment/', check_assignments),
]