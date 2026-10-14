"""Path reconstruction from a parent map."""

from __future__ import annotations

from collections.abc import Mapping

from .problem import Coordinate


def reconstruct_path(
    parents: Mapping[Coordinate, Coordinate | None], goal: Coordinate
) -> tuple[Coordinate, ...]:
    """Walk parent links from ``goal`` back to the start and return start -> goal.

    The start node is the one whose parent is ``None``. Raises ``ValueError`` if
    the chain is broken or loops, which would indicate a bug in the search.
    """
    path: list[Coordinate] = []
    current: Coordinate | None = goal
    while current is not None:
        if len(path) > len(parents):
            raise ValueError("Parent links contain a cycle.")
        if current not in parents:
            raise ValueError(f"No parent recorded for {tuple(current)}.")
        path.append(current)
        current = parents[current]
    path.reverse()
    return tuple(path)
