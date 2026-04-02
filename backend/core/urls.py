
from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/v1/',include('tickets.urls')),
    path('api/v2/',include('users.urls')),
]