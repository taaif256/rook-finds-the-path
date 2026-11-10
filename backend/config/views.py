"""Project-level API views that do not belong to a single feature app."""

from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.permissions import AllowAny
SERVICE_NAME = "chessboard-robot-navigation-api"
API_VERSION = "v1"


class HealthCheckView(APIView):
    """``GET /api/v1/health/`` - report that the backend service is up."""
    permission_classes = [AllowAny] # <--- Add this class attribute
    def get(self, request: Request) -> Response:
        return Response(
            {
                "status": "ok",
                "service": SERVICE_NAME,
                "api_version": API_VERSION,
            }
        )
