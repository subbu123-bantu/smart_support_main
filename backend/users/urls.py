from .views import RegisterView
from django.urls import path,include
urlpatterns = [
    path('signup/', RegisterView.as_view())
]
