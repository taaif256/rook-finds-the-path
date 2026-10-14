"""A* Search.

Orders the frontier by ``f(n) = g(n) + h(n)``: the cost paid so far plus the
estimated cost remaining. With four-directional unit-cost moves and the
Manhattan heuristic (admissible and consistent) the first time the goal is
taken from the frontier its path is a **shortest path**, and no explored node
ever needs to be explored again.
"""

from __future__ import annotations

from .events import EventRecorder
from .frontier import PriorityFrontier
from .heuristics import Heuristic, manhattan_distance
from .path import reconstruct_path
from .problem import MOVE_COST, Coordinate, SearchProblem
from .result import AlgorithmId, SearchResult


def a_star_search(problem: SearchProblem, heuristic: Heuristic = manhattan_distance) -> SearchResult:
    start, goal = problem.start, problem.end
    recorder = EventRecorder()
    frontier = PriorityFrontier()

    closed_set: set[Coordinate] = set()
    g_scores: dict[Coordinate, int] = {start: 0}
    parents: dict[Coordinate, Coordinate | None] = {start: None}

    start_h = heuristic(start, goal)
    frontier.push(start, start_h, start_h)
    recorder.open(start, 0, start_h, start_h)

    while frontier:
        current = frontier.pop()
        if current in closed_set:
            continue  # stale entry: a cheaper route to this node was explored first

        closed_set.add(current)
        g = g_scores[current]
        h = heuristic(current, goal)
        recorder.close(current, g, h, g + h)
        if current == goal:
            return SearchResult(AlgorithmId.ASTAR, reconstruct_path(parents, goal), recorder.events)

        for neighbor in problem.neighbors(current):
            if neighbor in closed_set:
                continue
            tentative_g = g + MOVE_COST
            known_g = g_scores.get(neighbor)
            if known_g is not None and tentative_g >= known_g:
                continue  # not better than the route we already know
            g_scores[neighbor] = tentative_g
            parents[neighbor] = current
            neighbor_h = heuristic(neighbor, goal)
            frontier.push(neighbor, tentative_g + neighbor_h, neighbor_h)
            recorder.open(neighbor, tentative_g, neighbor_h, tentative_g + neighbor_h)

    return SearchResult(AlgorithmId.ASTAR, (), recorder.events)
