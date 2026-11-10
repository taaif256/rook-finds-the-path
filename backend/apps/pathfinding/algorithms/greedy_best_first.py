"""Greedy Best-First Search (GBFS).

Orders the frontier purely by the heuristic, ``f(n) = h(n)``, always exploring
the node that looks closest to the goal. It is fast and often finds a path, but
it ignores the cost already paid, so the path it returns is **not guaranteed to
be the shortest**.
"""

from __future__ import annotations

from .events import EventRecorder
from .frontier import PriorityFrontier
from .heuristics import Heuristic, manhattan_distance
from .path import reconstruct_path
from .problem import MOVE_COST, Coordinate, SearchProblem
from .result import AlgorithmId, SearchResult


def greedy_best_first_search(
    problem: SearchProblem, heuristic: Heuristic = manhattan_distance
) -> SearchResult:
    start, goal = problem.start, problem.end
    recorder = EventRecorder()
    frontier = PriorityFrontier()

    open_set: set[Coordinate] = set()  # discovered, waiting in the frontier
    closed_set: set[Coordinate] = set()  # already explored, never expanded again
    parents: dict[Coordinate, Coordinate | None] = {start: None}
    # Cost of the route actually discovered to each node. Reported for display
    # only; GBFS never uses it to choose what to explore.
    route_cost: dict[Coordinate, int] = {start: 0}

    start_h = heuristic(start, goal)
    frontier.push(start, start_h, start_h)
    open_set.add(start)
    recorder.open(start, 0, start_h, start_h)

    while frontier:
        current = frontier.pop()
        open_set.discard(current)
        closed_set.add(current)

        h = heuristic(current, goal)
        recorder.close(current, route_cost[current], h, h)
        if current == goal:
            return SearchResult(AlgorithmId.GBFS, reconstruct_path(parents, goal), recorder.events)

        for neighbor in problem.neighbors(current):
            if neighbor in open_set or neighbor in closed_set:
                continue  # each node is discovered, and so explored, at most once
            parents[neighbor] = current
            route_cost[neighbor] = route_cost[current] + MOVE_COST
            neighbor_h = heuristic(neighbor, goal)
            frontier.push(neighbor, neighbor_h, neighbor_h)
            open_set.add(neighbor)
            recorder.open(neighbor, route_cost[neighbor], neighbor_h, neighbor_h)

    return SearchResult(AlgorithmId.GBFS, (), recorder.events)
