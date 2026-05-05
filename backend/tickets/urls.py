from django.urls import path

from .views import (
    TicketViewSet,
    CategoryViewSet,
    TicketCommentViewSet,
    predict_view,
    ticket_stats,
    assign_ticket,
    ticket_prediction_feedback,
    prediction_stats,
    test_backend,
)

ticket_list = TicketViewSet.as_view({
    "get": "list",
    "post": "create",
})

ticket_detail = TicketViewSet.as_view({
    "get": "retrieve",
    "put": "update",
    "patch": "partial_update",
})

category_list = CategoryViewSet.as_view({
    "get": "list",
    "post": "create",
})

ticket_comments = TicketCommentViewSet.as_view({
    "get": "list",
    "post": "create",
})

ticket_comment_detail = TicketCommentViewSet.as_view({
    "delete": "destroy",
})

urlpatterns = [
    path("test/", test_backend.as_view(), name="test-backend"),
    path("", ticket_list, name="ticket-list"),
    path("<int:pk>/", ticket_detail, name="ticket-detail"),
    path("categories/", category_list, name="category-list"),
    path("predict/", predict_view, name="predict"),
    path("stats/", ticket_stats, name="ticket-stats"),
    path("prediction-stats/", prediction_stats, name="prediction-stats"),

    path("<int:ticket_id>/assign/", assign_ticket, name="assign-ticket"),
    path("<int:ticket_id>/comments/", ticket_comments, name="ticket-comments"),
    path("<int:ticket_id>/comments/<int:pk>/", ticket_comment_detail, name="ticket-comment-detail"),
    path(
        "<int:ticket_id>/prediction-feedback/",
        ticket_prediction_feedback,
        name="ticket-prediction-feedback",
    ),
]
