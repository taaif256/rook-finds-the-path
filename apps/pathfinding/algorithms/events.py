"""The ordered record of what a search did, kept apart from its internal data."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum

from .problem import Coordinate


class EventKind(Enum):
    OPEN = "open"
    CLOSED = "closed"


@dataclass(frozen=True, slots=True)
class SearchEvent:
    """One step of a search.

    ``step`` is a single sequence shared by open and closed events (0, 1, 2, ...),
    so the two kinds can always be merged back into their original order.
    ``f`` is the priority the algorithm used: ``h`` for GBFS, ``g + h`` for A*.
    """

    step: int
    kind: EventKind
    node: Coordinate
    g: int
    h: int
    f: int


class EventRecorder:
    """Collects events and numbers them in the order they are recorded."""

    def __init__(self) -> None:
        self._events: list[SearchEvent] = []

    def open(self, node: Coordinate, g: int, h: int, f: int) -> None:
        """Record that ``node`` entered (or improved its place in) the frontier."""
        self._record(EventKind.OPEN, node, g, h, f)

    def close(self, node: Coordinate, g: int, h: int, f: int) -> None:
        """Record that ``node`` was taken from the frontier and explored."""
        self._record(EventKind.CLOSED, node, g, h, f)

    def _record(
        self, kind: EventKind, node: Coordinate, g: int, h: int, f: int
    ) -> None:
        self._events.append(SearchEvent(len(self._events), kind, node, g, h, f))

    @property
    def events(self) -> tuple[SearchEvent, ...]:
        return tuple(self._events)
