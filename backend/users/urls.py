from django.urls import path
from .views import (
    AgentListView,
    AgentProfileUpdateView,
    ChangeEmailView,
    ForgotPasswordView,
    LoginView,
    LogoutView,
    RegisterView,
    ResetPasswordView,
)

urlpatterns = [
    path('login/', LoginView.as_view()),
    path('logout/', LogoutView.as_view()),
    path('register/', RegisterView.as_view()),
    path('forgot-password/', ForgotPasswordView.as_view()),
    path('reset-password/', ResetPasswordView.as_view()),
    path('change-email/', ChangeEmailView.as_view()),
    path('agents/', AgentListView.as_view()),
    path('agents/<int:agent_id>/', AgentProfileUpdateView.as_view()),
]
