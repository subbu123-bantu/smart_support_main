
from django.contrib import admin
from django.urls import path, include
from tickets.views import test_backend

urlpatterns = [
    path('', test_backend.as_view(), name='backend-home'),
    path('admin/', admin.site.urls),
    path('api/',include('tickets.urls')),
    path('api/',include('users.urls')),
]
