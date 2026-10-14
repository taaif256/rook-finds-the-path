"""Root URL configuration. All API routes are versioned under ``/api/v1/``."""

from django.urls import include, path

urlpatterns = [
    path("api/v1/", include("config.api_v1_urls")),
]
