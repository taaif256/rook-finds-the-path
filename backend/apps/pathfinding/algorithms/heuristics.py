"""Heuristic functions for grid search."""

from __future__ import annotations

from collections.abc import Callable

from .problem import Coordinate

Heuristic = Callable[[Coordinate, Coordinate], int]


def manhattan_distance(a: Coordinate, b: Coordinate) -> int:
    """``|row difference| + |col difference|``.

    Admissible and consistent for four-directional movement with unit costs,
    which is what makes A* optimal here.
    """
    return abs(a.row - b.row) + abs(a.col - b.col)
