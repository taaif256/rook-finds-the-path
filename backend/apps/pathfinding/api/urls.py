"""Routes for the pathfinding feature, mounted at ``/api/v1/pathfinding/``."""

from django.urls import path

from apps.pathfinding.api.views import PathfindingRunView

app_name = "pathfinding"

urlpatterns = [
    path("run/", PathfindingRunView.as_view(), name="run"),
]
