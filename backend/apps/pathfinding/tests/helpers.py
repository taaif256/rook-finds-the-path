"""Shared test utilities: grid fixtures, an independent BFS oracle, invariant checks."""

from __future__ import annotations

import copy
import logging
import random
import textwrap
import unittest
from collections import deque

from rest_framework.test import APISimpleTestCase

from apps.pathfinding.algorithms import (
    AlgorithmId,
    Coordinate,
    EventKind,
    SearchProblem,
    SearchResult,
    manhattan_distance,
)


def make_problem(rows, cols, start, end, barriers=()) -> SearchProblem:
    return SearchProblem(rows, cols, start, end, frozenset(barriers))


def parse_grid(text: str) -> SearchProblem:
    """Build a problem from ASCII art: ``S`` start, ``E`` end, ``#`` barrier, ``.`` open."""
    lines = [line.strip() for line in textwrap.dedent(text).strip().splitlines()]
    cols = len(lines[0])
    assert all(len(line) == cols for line in lines), "ragged grid fixture"
    start = end = None
    barriers = set()
    for r, line in enumerate(lines):
        for c, char in enumerate(line):
            if char == "S":
                start = Coordinate(r, c)
            elif char == "E":
                end = Coordinate(r, c)
            elif char == "#":
                barriers.add(Coordinate(r, c))
            else:
                assert char == ".", f"unknown fixture character {char!r}"
    assert start is not None and end is not None, "fixture needs S and E"
    return SearchProblem(len(lines), cols, start, end, frozenset(barriers))


def bfs_search(problem: SearchProblem) -> tuple[int | None, set[Coordinate]]:
    """Independent oracle: (shortest path length in moves or None, reachable cells).

    Deliberately shares no code with the algorithms under test beyond ``neighbors``.
    """
    queue = deque([(problem.start, 0)])
    seen = {problem.start}
    shortest = None
    while queue:
        node, dist = queue.popleft()
        if node == problem.end and shortest is None:
            shortest = dist
        for neighbor in problem.neighbors(node):
            if neighbor not in seen:
                seen.add(neighbor)
                queue.append((neighbor, dist + 1))
    return shortest, seen


def random_problem(rng: random.Random) -> SearchProblem:
    while True:
        rows, cols = rng.randint(1, 9), rng.randint(1, 9)
        if rows * cols >= 2:
            break
    cells = [Coordinate(r, c) for r in range(rows) for c in range(cols)]
    start, end = rng.sample(cells, 2)
    density = rng.choice([0, 0.1, 0.2, 0.3, 0.4])
    barriers = frozenset(c for c in cells if c not in (start, end) and rng.random() < density)
    return SearchProblem(rows, cols, start, end, barriers)


class SearchAssertions(unittest.TestCase):
    """Mixin with the invariants every algorithm's output must satisfy."""

    def assertValidPath(self, problem: SearchProblem, result: SearchResult) -> None:
        path = result.path
        if not result.path_found:
            self.assertEqual(path, ())
            self.assertEqual((result.path_length, result.path_cost), (0, 0))
            return
        self.assertEqual(path[0], problem.start)
        self.assertEqual(path[-1], problem.end)
        self.assertEqual(len(set(path)), len(path), "path revisits a cell")
        for cell in path:
            self.assertTrue(problem.is_walkable(cell), f"{tuple(cell)} is not walkable")
        for a, b in zip(path, path[1:]):
            self.assertEqual(manhattan_distance(a, b), 1, f"{tuple(a)} -> {tuple(b)} is not one step")
        self.assertEqual(result.path_length, len(path) - 1)
        self.assertEqual(result.path_cost, result.path_length)

    def assertEventInvariants(self, problem: SearchProblem, result: SearchResult) -> None:
        events = result.events
        self.assertTrue(events, "a search always records at least the start node")
        self.assertEqual([e.step for e in events], list(range(len(events))))

        first = events[0]
        self.assertEqual((first.kind, first.node, first.g), (EventKind.OPEN, problem.start, 0))

        # node -> its current priority while it waits in the frontier (latest open event wins)
        waiting: dict[Coordinate, int] = {}
        closed: list[Coordinate] = []
        for event in events:
            self.assertTrue(problem.is_walkable(event.node), f"event on non-walkable {tuple(event.node)}")
            self.assertEqual(event.h, manhattan_distance(event.node, problem.end))
            expected_f = event.h if result.algorithm is AlgorithmId.GBFS else event.g + event.h
            self.assertEqual(event.f, expected_f)
            if event.kind is EventKind.OPEN:
                waiting[event.node] = event.f
            else:
                self.assertIn(event.node, waiting, "closed without waiting in the frontier")
                self.assertEqual(waiting.pop(event.node), event.f)
                # Defining property: the explored node had the best priority in the frontier
                # (lowest h for GBFS, lowest g + h for A*).
                self.assertLessEqual(
                    event.f,
                    min(waiting.values(), default=event.f),
                    f"step {event.step}: {tuple(event.node)} was not the best frontier node",
                )
                closed.append(event.node)
        self.assertEqual(len(closed), len(set(closed)), "a node was closed twice")

        # open/closed views partition the ordered history
        self.assertEqual(len(result.open_events) + len(result.closed_events), len(events))
        self.assertEqual(result.explored_nodes, len(closed))

        closed_g = {e.node: e.g for e in result.closed_events}
        if result.path_found:
            last = events[-1]
            self.assertEqual((last.kind, last.node), (EventKind.CLOSED, problem.end))
            self.assertEqual(last.g, result.path_length)
            for index, cell in enumerate(result.path):
                self.assertIn(cell, closed_g, "path cell was never explored")
                self.assertEqual(closed_g[cell], index, "g of a path cell must equal its index")
        else:
            self.assertNotIn(problem.end, closed_g)


# --- API test support ----------------------------------------------------------

RUN_URL = "/api/v1/pathfinding/run/"
ANGULAR_ORIGIN = "http://localhost:4200"

# The example request from the project spec: a 10x10 board with a short wall.
SPEC_EXAMPLE = {
    "algorithm": "astar",
    "grid": {"rows": 10, "cols": 10},
    "start": {"row": 0, "col": 0},
    "end": {"row": 9, "col": 9},
    "barriers": [{"row": 2, "col": 3}, {"row": 3, "col": 3}, {"row": 4, "col": 3}],
    "movement": "four_directional",
}


def run_payload(**overrides):
    """A valid run request (the spec example) with some fields replaced."""
    payload = copy.deepcopy(SPEC_EXAMPLE)
    payload.update(overrides)
    return payload


def without(payload, *keys):
    return {key: value for key, value in payload.items() if key not in keys}


def to_payload(problem: SearchProblem, algorithm: str = "astar") -> dict:
    """Describe a ``SearchProblem`` as an API request body."""
    return {
        "algorithm": algorithm,
        "grid": {"rows": problem.rows, "cols": problem.cols},
        "start": {"row": problem.start.row, "col": problem.start.col},
        "end": {"row": problem.end.row, "col": problem.end.col},
        "barriers": [{"row": b.row, "col": b.col} for b in sorted(problem.barriers)],
    }


class ApiTestCase(APISimpleTestCase):
    """Base for endpoint tests. Silences Django's expected 4xx request warnings."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls._request_logger = logging.getLogger("django.request")
        cls._previous_level = cls._request_logger.level
        cls._request_logger.setLevel(logging.CRITICAL)

    @classmethod
    def tearDownClass(cls):
        cls._request_logger.setLevel(cls._previous_level)
        super().tearDownClass()

    def run_request(self, payload):
        return self.client.post(RUN_URL, payload, format="json")

    def assertRejected(self, response, *expected_keys, status=400, message="Invalid request."):
        """Assert the standard error envelope, with errors on exactly ``expected_keys``."""
        self.assertEqual(response.status_code, status)
        self.assertEqual(response["Content-Type"], "application/json")
        body = response.json()
        self.assertEqual(set(body), {"status", "message", "errors"})
        self.assertEqual(body["status"], "error")
        if message is not None:
            self.assertEqual(body["message"], message)
        self.assertEqual(set(body["errors"]), set(expected_keys))
        for field, messages in body["errors"].items():
            self.assertIsInstance(messages, list, field)
            self.assertTrue(messages, field)
            for text in messages:
                self.assertIsInstance(text, str, field)
                self.assertTrue(text.strip(), field)
        return body
