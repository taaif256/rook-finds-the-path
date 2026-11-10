"""The service layer and the response formatter, tested without HTTP."""

import json
import unittest

from apps.pathfinding.algorithms import ALGORITHMS, AlgorithmId, Coordinate
from apps.pathfinding.services.pathfinding_service import PathfindingRun, run_pathfinding
from apps.pathfinding.services.visualization_serializer import (
    build_run_response,
    coordinate_to_dict,
    event_to_dict,
)

from .helpers import make_problem, parse_grid


def fake_clock(*readings):
    values = iter(readings)
    return lambda: next(values)


class RunPathfindingTests(unittest.TestCase):
    def test_runs_the_requested_algorithm(self):
        problem = parse_grid("S...\n.##.\n...E")
        for algorithm_id, algorithm in ALGORITHMS.items():
            with self.subTest(algorithm=algorithm_id.value):
                run = run_pathfinding(algorithm_id, problem)
                self.assertEqual(run.result, algorithm(problem))
                self.assertEqual(run.result.algorithm, algorithm_id)
                self.assertIs(run.problem, problem)

    def test_execution_time_is_the_elapsed_clock_time_in_milliseconds(self):
        problem = make_problem(3, 3, (0, 0), (2, 2))
        run = run_pathfinding(AlgorithmId.ASTAR, problem, clock=fake_clock(10.0, 10.25))
        self.assertAlmostEqual(run.execution_time_ms, 250.0)

    def test_the_clock_is_read_only_around_the_search(self):
        readings = []

        def clock():
            readings.append(len(readings))
            return float(len(readings))

        run_pathfinding(AlgorithmId.GBFS, make_problem(3, 3, (0, 0), (2, 2)), clock=clock)
        self.assertEqual(len(readings), 2)

    def test_real_clock_gives_a_non_negative_time(self):
        run = run_pathfinding(AlgorithmId.ASTAR, make_problem(5, 5, (0, 0), (4, 4)))
        self.assertGreaterEqual(run.execution_time_ms, 0)


class SerializerHelperTests(unittest.TestCase):
    def test_coordinate_to_dict(self):
        self.assertEqual(coordinate_to_dict(Coordinate(3, 7)), {"row": 3, "col": 7})

    def test_event_to_dict(self):
        run = run_pathfinding(AlgorithmId.ASTAR, make_problem(1, 3, (0, 0), (0, 2)))
        self.assertEqual(
            event_to_dict(run.result.events[0]),
            {"step": 0, "node": {"row": 0, "col": 0}, "g": 0, "h": 2, "f": 2},
        )


class BuildRunResponseTests(unittest.TestCase):
    def build(self, problem, algorithm_id=AlgorithmId.ASTAR, elapsed_ms=1.5):
        run = run_pathfinding(algorithm_id, problem, clock=fake_clock(0.0, elapsed_ms / 1000))
        return run, build_run_response(run)

    def test_found_path_response(self):
        problem = make_problem(1, 4, (0, 0), (0, 3))
        run, body = self.build(problem)
        self.assertEqual(list(body), [
            "algorithm", "status", "path_found", "start", "end",
            "open_events", "closed_events", "path", "metrics",
        ])
        self.assertEqual(body["algorithm"], "astar")
        self.assertEqual(body["status"], "success")
        self.assertIs(body["path_found"], True)
        self.assertEqual(body["path"], [{"row": 0, "col": c} for c in range(4)])
        self.assertEqual(body["metrics"], {"explored_nodes": 4, "path_length": 3, "path_cost": 3, "execution_time_ms": 1.5})

    def test_open_and_closed_events_are_split_but_keep_their_shared_steps(self):
        _, body = self.build(make_problem(1, 3, (0, 0), (0, 2)))
        self.assertEqual([e["step"] for e in body["open_events"]], [0, 2, 4])
        self.assertEqual([e["step"] for e in body["closed_events"]], [1, 3, 5])

    def test_no_path_response(self):
        _, body = self.build(parse_grid("S#E"))
        self.assertIs(body["path_found"], False)
        self.assertEqual(body["path"], [])
        self.assertEqual(body["metrics"]["path_length"], 0)
        self.assertEqual(body["metrics"]["path_cost"], 0)
        self.assertEqual(body["metrics"]["explored_nodes"], 1)

    def test_execution_time_is_rounded_to_three_decimals(self):
        _, body = self.build(make_problem(3, 3, (0, 0), (2, 2)), elapsed_ms=1.23456)
        self.assertEqual(body["metrics"]["execution_time_ms"], 1.235)

    def test_response_is_json_serialisable_and_round_trips(self):
        for algorithm_id in AlgorithmId:
            _, body = self.build(parse_grid("S...\n.##.\n...E"), algorithm_id)
            self.assertEqual(json.loads(json.dumps(body)), body)

    def test_response_reports_the_problem_start_and_end(self):
        run, body = self.build(make_problem(4, 6, (3, 1), (0, 5)))
        self.assertEqual((body["start"], body["end"]), ({"row": 3, "col": 1}, {"row": 0, "col": 5}))
        self.assertIsInstance(run, PathfindingRun)


if __name__ == "__main__":
    unittest.main()
