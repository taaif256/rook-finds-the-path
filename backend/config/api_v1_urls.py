"""Routes for version 1 of the REST API, mounted at ``/api/v1/``."""

from django.urls import include, path

from config.views import HealthCheckView

urlpatterns = [
    path("health/", HealthCheckView.as_view(), name="health"),
    path('auth/', include('djoser.urls')),
    path('auth/', include('djoser.urls.jwt')),
    path("pathfinding/", include("apps.pathfinding.api.urls")),
]
