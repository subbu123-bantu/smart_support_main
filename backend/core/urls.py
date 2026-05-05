
from django.contrib import admin
from django.urls import include, path

from tickets.views import test_backend

urlpatterns = [
    path("", test_backend.as_view(), name="backend-home"),
    path("admin/", admin.site.urls),
    path("api/auth/", include("users.urls")),
    path("api/tickets/", include("tickets.urls")),
]
