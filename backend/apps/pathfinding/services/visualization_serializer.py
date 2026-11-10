"""Turns a finished search into the JSON-ready response the frontend replays.

This is the only place that knows the response shape. The algorithms produce one
ordered history of events; here it is split into ``open_events`` and
``closed_events`` (each event keeps its shared ``step`` so the two can be merged
back into the original order).
"""

from __future__ import annotations

from typing import Any

from apps.pathfinding.algorithms import Coordinate, SearchEvent

from .pathfinding_service import PathfindingRun

EXECUTION_TIME_DECIMALS = 3


def coordinate_to_dict(coordinate: Coordinate) -> dict[str, int]:
    return {"row": coordinate.row, "col": coordinate.col}


def event_to_dict(event: SearchEvent) -> dict[str, Any]:
    return {
        "step": event.step,
        "node": coordinate_to_dict(event.node),
        "g": event.g,
        "h": event.h,
        "f": event.f,
    }


def build_run_response(run: PathfindingRun) -> dict[str, Any]:
    """The body of a successful ``POST /api/v1/pathfinding/run/``."""
    result = run.result
    return {
        "algorithm": result.algorithm.value,
        "status": "success",
        "path_found": result.path_found,
        "start": coordinate_to_dict(run.problem.start),
        "end": coordinate_to_dict(run.problem.end),
        "open_events": [event_to_dict(event) for event in result.open_events],
        "closed_events": [event_to_dict(event) for event in result.closed_events],
        "path": [coordinate_to_dict(cell) for cell in result.path],
        "metrics": {
            "explored_nodes": result.explored_nodes,
            "path_length": result.path_length,
            "path_cost": result.path_cost,
            "execution_time_ms": round(run.execution_time_ms, EXECUTION_TIME_DECIMALS),
        },
    }
