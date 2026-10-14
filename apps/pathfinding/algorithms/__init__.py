"""Pure pathfinding logic. Knows nothing about HTTP, JSON or the UI."""

from .astar import a_star_search
from .events import EventKind, SearchEvent
from .greedy_best_first import greedy_best_first_search
from .heuristics import manhattan_distance
from .problem import (
    GRID_SIZE_ERROR,
    MAX_GRID_SIZE,
    MIN_GRID_SIZE,
    Coordinate,
    InvalidSearchProblemError,
    SearchProblem,
)
from .registry import ALGORITHMS, UnknownAlgorithmError, get_algorithm
from .result import AlgorithmId, SearchResult

__all__ = [
    "ALGORITHMS",
    "AlgorithmId",
    "Coordinate",
    "EventKind",
    "GRID_SIZE_ERROR",
    "InvalidSearchProblemError",
    "MAX_GRID_SIZE",
    "MIN_GRID_SIZE",
    "SearchEvent",
    "SearchProblem",
    "SearchResult",
    "UnknownAlgorithmError",
    "a_star_search",
    "get_algorithm",
    "greedy_best_first_search",
    "manhattan_distance",
]
