"""What a search returns."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum

from .events import EventKind, SearchEvent
from .problem import MOVE_COST, Coordinate


class AlgorithmId(Enum):
    """Identifiers accepted by the API."""

    GBFS = "gbfs"
    ASTAR = "astar"


@dataclass(frozen=True)
class SearchResult:
    """Outcome of one search run.

    ``path`` runs from start to end inclusive and is empty when no path exists.
    ``events`` is the full ordered history for visualization.
    """

    algorithm: AlgorithmId
    path: tuple[Coordinate, ...]
    events: tuple[SearchEvent, ...]

    @property
    def path_found(self) -> bool:
        return bool(self.path)

    @property
    def path_length(self) -> int:
        """Number of moves in the path (cells - 1); 0 when there is no path."""
        return max(len(self.path) - 1, 0)

    @property
    def path_cost(self) -> int:
        """Total movement cost of the path; 0 when there is no path."""
        return self.path_length * MOVE_COST

    @property
    def open_events(self) -> tuple[SearchEvent, ...]:
        return tuple(event for event in self.events if event.kind is EventKind.OPEN)

    @property
    def closed_events(self) -> tuple[SearchEvent, ...]:
        return tuple(event for event in self.events if event.kind is EventKind.CLOSED)

    @property
    def explored_nodes(self) -> int:
        """Number of nodes taken from the frontier and explored (includes the end node if reached)."""
        return len(self.closed_events)
