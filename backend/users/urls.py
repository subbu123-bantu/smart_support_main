from django.urls import path
from .views import (
    AgentListView,
    AgentProfileUpdateView,
    LoginView,
    LogoutView,
    RegisterView,
)

urlpatterns = [
    path('login/', LoginView.as_view()),
    path('logout/', LogoutView.as_view()),
    path('register/', RegisterView.as_view()),
    path('agents/', AgentListView.as_view()),
    path('agents/<int:agent_id>/', AgentProfileUpdateView.as_view()),
]
