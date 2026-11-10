"""HTTP layer for the pathfinding feature.

Views stay thin: validation lives in the serializer, searching in the service
layer, and the response shape in the visualization serializer.
"""

from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.pathfinding.api.serializers import PathfindingRequestSerializer
from apps.pathfinding.services.pathfinding_service import run_pathfinding
from apps.pathfinding.services.visualization_serializer import build_run_response


class PathfindingRunView(APIView):
    """``POST /api/v1/pathfinding/run/``: run a search and return its full event history."""

    def post(self, request: Request) -> Response:
        serializer = PathfindingRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        run = run_pathfinding(
            serializer.validated_data["algorithm"], serializer.validated_data["problem"]
        )
        return Response(build_run_response(run))
