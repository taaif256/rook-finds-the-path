"""The open frontier shared by both algorithms."""

from __future__ import annotations

import heapq
import itertools

from .problem import Coordinate


class PriorityFrontier:
    """A min-priority queue of nodes with deterministic tie-breaking.

    Entries are ordered by ``(f, h, insertion order)``: lowest priority first,
    then the node that looks closer to the goal, then the one discovered
    earliest. Fixing the tie-break makes every search reproducible, so
    animations and tests are stable.
    """

    def __init__(self) -> None:
        self._heap: list[tuple[int, int, int, Coordinate]] = []
        self._counter = itertools.count()

    def push(self, node: Coordinate, f: int, h: int) -> None:
        heapq.heappush(self._heap, (f, h, next(self._counter), node))

    def pop(self) -> Coordinate:
        return heapq.heappop(self._heap)[3]

    def __len__(self) -> int:
        return len(self._heap)

    def __bool__(self) -> bool:
        return bool(self._heap)
