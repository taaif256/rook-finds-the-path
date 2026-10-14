"""The search problem: a validated grid, start, end and barriers.

``SearchProblem`` is the single place where grid input is validated. Anything
that can be constructed is guaranteed to be searchable, so the algorithms never
need to defend against bad coordinates.
"""

from __future__ import annotations

from collections.abc import Iterable, Iterator
from dataclasses import dataclass
from typing import NamedTuple

MIN_GRID_SIZE = 1
MAX_GRID_SIZE = 50
GRID_SIZE_ERROR = f"Must be an integer between {MIN_GRID_SIZE} and {MAX_GRID_SIZE}."

# Every move costs 1 (four-directional movement only; no diagonals).
MOVE_COST = 1


class Coordinate(NamedTuple):
    """A zero-based grid position. ``row`` grows downward, ``col`` rightward."""

    row: int
    col: int


# Neighbour order is part of the deterministic behaviour of the search:
# up, down, left, right.
DIRECTIONS: tuple[tuple[int, int], ...] = ((-1, 0), (1, 0), (0, -1), (0, 1))


class InvalidSearchProblemError(ValueError):
    """Raised when grid input cannot describe a searchable problem.

    ``field`` uses the same names as the API request (``grid.rows``, ``start``,
    ``end``, ``barriers``) so the API layer can map the error to a request field.
    """

    def __init__(self, field: str, message: str) -> None:
        super().__init__(f"{field}: {message}")
        self.field = field
        self.message = message


def _is_int(value: object) -> bool:
    return isinstance(value, int) and not isinstance(value, bool)


def _as_coordinate(value: object, field: str) -> Coordinate:
    try:
        row, col = value  # type: ignore[misc]
    except (TypeError, ValueError):
        raise InvalidSearchProblemError(field, "Must be a (row, col) pair.") from None
    if not (_is_int(row) and _is_int(col)):
        raise InvalidSearchProblemError(field, "Row and col must be integers.")
    return Coordinate(row, col)


@dataclass(frozen=True)
class SearchProblem:
    """A grid with one start, one end and any number of barriers.

    Raises ``InvalidSearchProblemError`` if the grid size is outside
    ``MIN_GRID_SIZE``..``MAX_GRID_SIZE``, any coordinate is out of bounds or
    malformed, start equals end, or start/end sit on a barrier. Duplicate
    barriers are tolerated and collapsed.
    """

    rows: int
    cols: int
    start: Coordinate
    end: Coordinate
    barriers: frozenset[Coordinate] = frozenset()

    def __post_init__(self) -> None:
        for field, size in (("grid.rows", self.rows), ("grid.cols", self.cols)):
            if not _is_int(size) or not MIN_GRID_SIZE <= size <= MAX_GRID_SIZE:
                raise InvalidSearchProblemError(field, GRID_SIZE_ERROR)

        start = _as_coordinate(self.start, "start")
        end = _as_coordinate(self.end, "end")
        barriers = frozenset(_as_coordinate(item, "barriers") for item in self._iter_barriers())
        object.__setattr__(self, "start", start)
        object.__setattr__(self, "end", end)
        object.__setattr__(self, "barriers", barriers)

        for field, coordinate in (("start", start), ("end", end)):
            self._require_in_bounds(coordinate, field)
        for barrier in sorted(barriers):
            self._require_in_bounds(barrier, "barriers")

        if start == end:
            raise InvalidSearchProblemError("end", "End must be different from start.")
        if start in barriers:
            raise InvalidSearchProblemError("start", "Start cannot be on a barrier.")
        if end in barriers:
            raise InvalidSearchProblemError("end", "End cannot be on a barrier.")

    def _iter_barriers(self) -> Iterable[object]:
        try:
            return iter(self.barriers)
        except TypeError:
            raise InvalidSearchProblemError("barriers", "Must be a list of coordinates.") from None

    def _require_in_bounds(self, coordinate: Coordinate, field: str) -> None:
        if not self.in_bounds(coordinate):
            raise InvalidSearchProblemError(
                field, f"{tuple(coordinate)} is outside the {self.rows}x{self.cols} grid."
            )

    def in_bounds(self, coordinate: Coordinate) -> bool:
        return 0 <= coordinate.row < self.rows and 0 <= coordinate.col < self.cols

    def is_walkable(self, coordinate: Coordinate) -> bool:
        """True if the cell is on the grid and not a barrier."""
        return self.in_bounds(coordinate) and coordinate not in self.barriers

    def neighbors(self, coordinate: Coordinate) -> Iterator[Coordinate]:
        """Walkable four-directional neighbours, in the fixed ``DIRECTIONS`` order."""
        for d_row, d_col in DIRECTIONS:
            candidate = Coordinate(coordinate.row + d_row, coordinate.col + d_col)
            if self.is_walkable(candidate):
                yield candidate
