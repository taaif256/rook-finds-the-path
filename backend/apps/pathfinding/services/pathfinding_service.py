"""Runs a search and measures it. Knows nothing about HTTP or JSON."""

from __future__ import annotations

import time
from collections.abc import Callable
from dataclasses import dataclass

from apps.pathfinding.algorithms import AlgorithmId, SearchProblem, SearchResult, get_algorithm


@dataclass(frozen=True)
class PathfindingRun:
    """A finished search together with the problem it solved and how long it took."""

    problem: SearchProblem
    result: SearchResult
    execution_time_ms: float


def run_pathfinding(
    algorithm_id: AlgorithmId,
    problem: SearchProblem,
    *,
    clock: Callable[[], float] = time.perf_counter,
) -> PathfindingRun:
    """Run ``algorithm_id`` on ``problem``. ``clock`` returns seconds and is injectable for tests."""
    algorithm = get_algorithm(algorithm_id)
    started = clock()
    result = algorithm(problem)
    elapsed_ms = (clock() - started) * 1000
    return PathfindingRun(problem=problem, result=result, execution_time_ms=elapsed_ms)
