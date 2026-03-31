from .views import RegisterView, login_view
from django.urls import path,include
urlpatterns = [
    path('/api/login/',login_view),
    path('register/', RegisterView.as_view())
]