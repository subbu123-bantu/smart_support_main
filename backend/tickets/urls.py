from django.urls import path, include
from rest_framework.routers import DefaultRouter

from .views import (
    TicketViewSet,
    CategoryViewSet,
    TicketCommentViewSet,
    ticket_stats,
    assign_ticket,
    ticket_prediction_feedback,
    prediction_stats,
    test_backend,
)
from .ai import predict_ticket


router = DefaultRouter()
router.register(r"tickets", TicketViewSet, basename="ticket")
router.register(r"categories", CategoryViewSet, basename="category")

ticket_comments = TicketCommentViewSet.as_view({
    "get": "list",
    "post": "create",
})

ticket_comment_detail = TicketCommentViewSet.as_view({
    "delete": "destroy",
})

urlpatterns = [
    path("", include(router.urls)),

    path("test/", test_backend.as_view(), name="test-backend"),
    path("predict/", predict_ticket, name="predict-ticket"),
    path("stats/", ticket_stats, name="ticket-stats"),
    path("prediction-stats/", prediction_stats, name="prediction-stats"),

    path("tickets/<int:ticket_id>/assign/", assign_ticket, name="assign-ticket"),
    path("tickets/<int:ticket_id>/comments/", ticket_comments, name="ticket-comments"),
    path("tickets/<int:ticket_id>/comments/<int:pk>/", ticket_comment_detail, name="ticket-comment-detail"),
    path(
        "tickets/<int:ticket_id>/prediction-feedback/",
        ticket_prediction_feedback,
        name="ticket-prediction-feedback",
    ),
]