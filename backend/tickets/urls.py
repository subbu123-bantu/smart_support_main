from django.urls import path, include
from rest_framework.routers import DefaultRouter

from tickets.ai import predict_ticket
from .views import TicketViewSet, CategoryViewSet, TicketCommentViewSet
from .views import ticket_stats, assign_ticket, ticket_prediction_feedback

router = DefaultRouter()
router.register(r'tickets', TicketViewSet, basename='ticket')
router.register(r'categories', CategoryViewSet, basename='category')

ticket_comments = TicketCommentViewSet.as_view({
    "get": "list",
    "post": "create",
})

ticket_comment_detail = TicketCommentViewSet.as_view({
    "delete": "destroy",
})

urlpatterns = [
    path('', include(router.urls)),
    path('predict/',predict_ticket),
    path('stats/', ticket_stats),
    path('tickets/<int:ticket_id>/assign/', assign_ticket),
    


    path('tickets/<int:ticket_id>/comments/', ticket_comments, name='ticket-comments'),
    path('tickets/<int:ticket_id>/comments/<int:pk>/', ticket_comment_detail, name='ticket-comment-detail'),
    path("tickets/<int:ticket_id>/prediction-feedback/", ticket_prediction_feedback),
]