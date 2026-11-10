"""Request validation for ``POST /api/v1/pathfinding/run/``.

DRF checks the shape and types of the JSON. The grid rules (bounds, start/end
distinct, nothing on a barrier) are enforced once, by ``SearchProblem``; this
serializer only translates its errors into request-field errors.
"""

from __future__ import annotations

from typing import Any

from rest_framework import serializers

from apps.pathfinding.algorithms import (
    GRID_SIZE_ERROR,
    MAX_GRID_SIZE,
    MIN_GRID_SIZE,
    AlgorithmId,
    Coordinate,
    InvalidSearchProblemError,
    SearchProblem,
)

# A valid board cannot hold more barriers than it has cells. Capping the list also
# bounds how much work a single request can ask the server to do.
MAX_BARRIER_ENTRIES = MAX_GRID_SIZE * MAX_GRID_SIZE

SUPPORTED_MOVEMENT = "four_directional"
_ALGORITHM_IDS = [item.value for item in AlgorithmId]


class StrictIntegerField(serializers.IntegerField):
    """An integer that must really be a JSON integer.

    DRF's ``IntegerField`` would quietly accept ``"3"``, ``3.0`` and ``true``.
    """

    default_error_messages = {"invalid": "A valid integer is required."}

    def to_internal_value(self, data: Any) -> int:
        if isinstance(data, bool) or not isinstance(data, int):
            self.fail("invalid")
        return super().to_internal_value(data)


class CoordinateSerializer(serializers.Serializer):
    """``{"row": int, "col": int}``. Bounds are checked against the grid later."""

    row = StrictIntegerField()
    col = StrictIntegerField()


class GridSerializer(serializers.Serializer):
    rows = StrictIntegerField(
        min_value=MIN_GRID_SIZE,
        max_value=MAX_GRID_SIZE,
        error_messages={"min_value": GRID_SIZE_ERROR, "max_value": GRID_SIZE_ERROR},
    )
    cols = StrictIntegerField(
        min_value=MIN_GRID_SIZE,
        max_value=MAX_GRID_SIZE,
        error_messages={"min_value": GRID_SIZE_ERROR, "max_value": GRID_SIZE_ERROR},
    )


def _to_coordinate(data: dict[str, int]) -> Coordinate:
    return Coordinate(data["row"], data["col"])


class PathfindingRequestSerializer(serializers.Serializer):
    """Validates a run request.

    After ``is_valid()``, ``validated_data`` is ``{"algorithm": AlgorithmId,
    "problem": SearchProblem}``, ready for the service layer.
    """

    algorithm = serializers.ChoiceField(
        choices=_ALGORITHM_IDS,
        error_messages={
            "invalid_choice": 'Unknown algorithm "{input}". Valid algorithms: '
            + ", ".join(_ALGORITHM_IDS)
            + "."
        },
    )
    grid = GridSerializer()
    start = CoordinateSerializer()
    end = CoordinateSerializer()
    barriers = CoordinateSerializer(
        many=True, required=False, allow_empty=True, max_length=MAX_BARRIER_ENTRIES
    )
    movement = serializers.ChoiceField(
        choices=[SUPPORTED_MOVEMENT],
        required=False,
        default=SUPPORTED_MOVEMENT,
        error_messages={
            "invalid_choice": 'Unsupported movement "{input}". Only "'
            + SUPPORTED_MOVEMENT
            + '" is supported.'
        },
    )

    def validate(self, attrs: dict[str, Any]) -> dict[str, Any]:
        grid = attrs["grid"]
        try:
            problem = SearchProblem(
                rows=grid["rows"],
                cols=grid["cols"],
                start=_to_coordinate(attrs["start"]),
                end=_to_coordinate(attrs["end"]),
                barriers=frozenset(_to_coordinate(item) for item in attrs.get("barriers", [])),
            )
        except InvalidSearchProblemError as error:
            raise serializers.ValidationError({error.field: [error.message]}) from error
        return {"algorithm": AlgorithmId(attrs["algorithm"]), "problem": problem}
