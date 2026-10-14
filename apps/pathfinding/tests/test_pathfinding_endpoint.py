"""POST /api/v1/pathfinding/run/: successful runs and the shape of the response."""

import random

from apps.pathfinding.algorithms import ALGORITHMS, AlgorithmId, manhattan_distance

from .helpers import (
    ANGULAR_ORIGIN,
    RUN_URL,
    SPEC_EXAMPLE,
    ApiTestCase,
    bfs_search,
    parse_grid,
    random_problem,
    run_payload,
    to_payload,
    without,
)

RESPONSE_KEYS = {
    "algorithm", "status", "path_found", "start", "end",
    "open_events", "closed_events", "path", "metrics",
}
METRIC_KEYS = {"explored_nodes", "path_length", "path_cost", "execution_time_ms"}
EVENT_KEYS = {"step", "node", "g", "h", "f"}


def ev(step, row, col, g, h, f):
    return {"step": step, "node": {"row": row, "col": col}, "g": g, "h": h, "f": f}


def cell(row, col):
    return {"row": row, "col": col}


def merged_events(body):
    return sorted(body["open_events"] + body["closed_events"], key=lambda e: e["step"])


class ResponseShapeTests(ApiTestCase):
    def test_spec_example_succeeds_for_every_algorithm(self):
        for algorithm_id in AlgorithmId:
            with self.subTest(algorithm=algorithm_id.value):
                response = self.run_request(run_payload(algorithm=algorithm_id.value))
                self.assertEqual(response.status_code, 200)
                self.assertEqual(response["Content-Type"], "application/json")
                body = response.json()

                self.assertEqual(set(body), RESPONSE_KEYS)
                self.assertEqual(body["algorithm"], algorithm_id.value)
                self.assertEqual(body["status"], "success")
                self.assertIs(body["path_found"], True)
                self.assertEqual(body["start"], cell(0, 0))
                self.assertEqual(body["end"], cell(9, 9))
                self.assertEqual(set(body["metrics"]), METRIC_KEYS)

    def test_path_is_an_ordered_walk_from_start_to_end_avoiding_barriers(self):
        barriers = {(b["row"], b["col"]) for b in SPEC_EXAMPLE["barriers"]}
        for algorithm_id in AlgorithmId:
            with self.subTest(algorithm=algorithm_id.value):
                body = self.run_request(run_payload(algorithm=algorithm_id.value)).json()
                path = [(c["row"], c["col"]) for c in body["path"]]
                self.assertEqual(path[0], (0, 0))
                self.assertEqual(path[-1], (9, 9))
                self.assertFalse(set(path) & barriers)
                self.assertEqual(len(set(path)), len(path))
                for a, b in zip(path, path[1:]):
                    self.assertEqual(abs(a[0] - b[0]) + abs(a[1] - b[1]), 1)

    def test_astar_returns_the_shortest_path_for_the_spec_example(self):
        body = self.run_request(run_payload(algorithm="astar")).json()
        self.assertEqual(body["metrics"]["path_length"], 18)

    def test_metrics_are_consistent_with_the_rest_of_the_response(self):
        for algorithm_id in AlgorithmId:
            with self.subTest(algorithm=algorithm_id.value):
                body = self.run_request(run_payload(algorithm=algorithm_id.value)).json()
                metrics = body["metrics"]
                self.assertEqual(metrics["path_length"], len(body["path"]) - 1)
                self.assertEqual(metrics["path_cost"], metrics["path_length"])
                self.assertEqual(metrics["explored_nodes"], len(body["closed_events"]))
                self.assertIsInstance(metrics["execution_time_ms"], (int, float))
                self.assertGreaterEqual(metrics["execution_time_ms"], 0)

    def test_events_have_the_documented_shape_and_integer_types(self):
        body = self.run_request(run_payload()).json()
        for event in body["open_events"] + body["closed_events"]:
            self.assertEqual(set(event), EVENT_KEYS)
            self.assertEqual(set(event["node"]), {"row", "col"})
            for key in ("step", "g", "h", "f"):
                self.assertIs(type(event[key]), int, key)

    def test_open_and_closed_events_merge_back_into_one_ordered_history(self):
        for algorithm_id in AlgorithmId:
            with self.subTest(algorithm=algorithm_id.value):
                body = self.run_request(run_payload(algorithm=algorithm_id.value)).json()
                self.assertEqual([e["step"] for e in merged_events(body)], list(range(len(merged_events(body)))))
                # each list is itself already in order
                for events in (body["open_events"], body["closed_events"]):
                    steps = [e["step"] for e in events]
                    self.assertEqual(steps, sorted(steps))
                # the first event is the start node being opened, the last the end being closed
                self.assertEqual(merged_events(body)[0]["node"], body["start"])
                self.assertEqual(body["closed_events"][-1]["node"], body["end"])
                self.assertEqual(body["closed_events"][-1]["step"], merged_events(body)[-1]["step"])


class GoldenResponseTests(ApiTestCase):
    """Exact responses for a 2x2 board, so every field and tie-break is pinned down."""

    PAYLOAD = {
        "grid": {"rows": 2, "cols": 2},
        "start": cell(0, 0),
        "end": cell(1, 1),
        "barriers": [],
    }

    def exact(self, algorithm):
        body = self.run_request({"algorithm": algorithm, **self.PAYLOAD}).json()
        body["metrics"].pop("execution_time_ms")
        return body

    def test_astar(self):
        self.assertEqual(
            self.exact("astar"),
            {
                "algorithm": "astar",
                "status": "success",
                "path_found": True,
                "start": cell(0, 0),
                "end": cell(1, 1),
                "open_events": [ev(0, 0, 0, 0, 2, 2), ev(2, 1, 0, 1, 1, 2), ev(3, 0, 1, 1, 1, 2), ev(5, 1, 1, 2, 0, 2)],
                "closed_events": [ev(1, 0, 0, 0, 2, 2), ev(4, 1, 0, 1, 1, 2), ev(6, 1, 1, 2, 0, 2)],
                "path": [cell(0, 0), cell(1, 0), cell(1, 1)],
                "metrics": {"explored_nodes": 3, "path_length": 2, "path_cost": 2},
            },
        )

    def test_gbfs(self):
        self.assertEqual(
            self.exact("gbfs"),
            {
                "algorithm": "gbfs",
                "status": "success",
                "path_found": True,
                "start": cell(0, 0),
                "end": cell(1, 1),
                "open_events": [ev(0, 0, 0, 0, 2, 2), ev(2, 1, 0, 1, 1, 1), ev(3, 0, 1, 1, 1, 1), ev(5, 1, 1, 2, 0, 0)],
                "closed_events": [ev(1, 0, 0, 0, 2, 2), ev(4, 1, 0, 1, 1, 1), ev(6, 1, 1, 2, 0, 0)],
                "path": [cell(0, 0), cell(1, 0), cell(1, 1)],
                "metrics": {"explored_nodes": 3, "path_length": 2, "path_cost": 2},
            },
        )


class NoPathTests(ApiTestCase):
    BLOCKED = parse_grid(
        """
        S.#..
        ..#..
        ..#.E
        """
    )

    def test_no_path_is_a_successful_response_not_an_error(self):
        for algorithm_id in AlgorithmId:
            with self.subTest(algorithm=algorithm_id.value):
                response = self.run_request(to_payload(self.BLOCKED, algorithm_id.value))
                self.assertEqual(response.status_code, 200)
                body = response.json()
                self.assertEqual(body["status"], "success")
                self.assertIs(body["path_found"], False)
                self.assertEqual(body["path"], [])
                self.assertEqual(body["metrics"]["path_length"], 0)
                self.assertEqual(body["metrics"]["path_cost"], 0)

    def test_no_path_still_returns_the_whole_exploration_for_animation(self):
        _, reachable = bfs_search(self.BLOCKED)
        for algorithm_id in AlgorithmId:
            with self.subTest(algorithm=algorithm_id.value):
                body = self.run_request(to_payload(self.BLOCKED, algorithm_id.value)).json()
                explored = {(e["node"]["row"], e["node"]["col"]) for e in body["closed_events"]}
                self.assertEqual(explored, {(c.row, c.col) for c in reachable})
                self.assertEqual(body["metrics"]["explored_nodes"], len(reachable))
                self.assertNotIn(body["end"], [e["node"] for e in body["closed_events"]])
                self.assertEqual(body["open_events"][0]["node"], body["start"])

    def test_start_surrounded_by_barriers(self):
        problem = parse_grid(".#...\n#S#..\n.#..E")
        body = self.run_request(to_payload(problem)).json()
        self.assertIs(body["path_found"], False)
        self.assertEqual(body["metrics"]["explored_nodes"], 1)
        self.assertEqual(len(body["open_events"]), 1)


class OptionalFieldTests(ApiTestCase):
    def test_movement_defaults_to_four_directional(self):
        response = self.run_request(without(run_payload(), "movement"))
        self.assertEqual(response.status_code, 200)

    def test_barriers_may_be_omitted_or_empty(self):
        for payload in (without(run_payload(), "barriers"), run_payload(barriers=[])):
            with self.subTest(barriers=payload.get("barriers", "omitted")):
                body = self.run_request(payload).json()
                self.assertIs(body["path_found"], True)
                self.assertEqual(body["metrics"]["path_length"], 18)

    def test_duplicate_barriers_are_tolerated(self):
        duplicated = run_payload(barriers=SPEC_EXAMPLE["barriers"] * 3)
        self.assertEqual(
            self.run_request(duplicated).json()["path"],
            self.run_request(run_payload()).json()["path"],
        )

    def test_unknown_extra_fields_are_ignored(self):
        self.assertEqual(self.run_request(run_payload(debug=True, note="hi")).status_code, 200)

    def test_barrier_list_at_the_size_limit_is_accepted(self):
        self.assertEqual(self.run_request(run_payload(barriers=[cell(5, 5)] * 2500)).status_code, 200)


class GridSizeTests(ApiTestCase):
    def test_smallest_boards(self):
        for rows, cols, end in ((1, 2, cell(0, 1)), (2, 1, cell(1, 0))):
            with self.subTest(rows=rows, cols=cols):
                payload = {
                    "algorithm": "astar", "grid": {"rows": rows, "cols": cols},
                    "start": cell(0, 0), "end": end, "barriers": [],
                }
                body = self.run_request(payload).json()
                self.assertIs(body["path_found"], True)
                self.assertEqual(body["metrics"]["path_length"], 1)

    def test_single_row_and_single_column_boards(self):
        for payload in (
            {"algorithm": "astar", "grid": {"rows": 1, "cols": 8}, "start": cell(0, 0), "end": cell(0, 7), "barriers": []},
            {"algorithm": "gbfs", "grid": {"rows": 8, "cols": 1}, "start": cell(7, 0), "end": cell(0, 0), "barriers": []},
        ):
            with self.subTest(grid=payload["grid"]):
                body = self.run_request(payload).json()
                self.assertEqual(body["metrics"]["path_length"], 7)

    def test_largest_board(self):
        payload = {
            "algorithm": "astar", "grid": {"rows": 50, "cols": 50},
            "start": cell(0, 0), "end": cell(49, 49), "barriers": [],
        }
        response = self.run_request(payload)
        self.assertEqual(response.status_code, 200)
        body = response.json()
        self.assertEqual(body["metrics"]["path_length"], 98)
        self.assertEqual(len(merged_events(body)), len(body["open_events"]) + len(body["closed_events"]))


class BehaviourTests(ApiTestCase):
    def test_same_request_gives_the_same_result_apart_from_timing(self):
        first = self.run_request(run_payload()).json()
        second = self.run_request(run_payload()).json()
        first["metrics"].pop("execution_time_ms")
        second["metrics"].pop("execution_time_ms")
        self.assertEqual(first, second)

    def test_requests_are_stateless(self):
        blocked = {
            "algorithm": "astar", "grid": {"rows": 1, "cols": 5},
            "start": cell(0, 0), "end": cell(0, 4), "barriers": [cell(0, 2)],
        }
        open_row = {**blocked, "barriers": []}
        self.assertIs(self.run_request(blocked).json()["path_found"], False)
        self.assertIs(self.run_request(open_row).json()["path_found"], True)
        self.assertIs(self.run_request(blocked).json()["path_found"], False)

    def test_response_is_readable_by_the_angular_dev_server(self):
        response = self.client.post(RUN_URL, run_payload(), format="json", headers={"Origin": ANGULAR_ORIGIN})
        self.assertEqual(response.headers.get("Access-Control-Allow-Origin"), ANGULAR_ORIGIN)

    def test_random_boards_through_http_match_the_algorithms_and_the_bfs_oracle(self):
        rng = random.Random(4242)
        for _ in range(120):
            problem = random_problem(rng)
            shortest, _ = bfs_search(problem)
            for algorithm_id, algorithm in ALGORITHMS.items():
                body = self.run_request(to_payload(problem, algorithm_id.value)).json()
                direct = algorithm(problem)
                context = f"{algorithm_id.value} on {problem}"

                self.assertEqual(body["path_found"], shortest is not None, context)
                if algorithm_id is AlgorithmId.ASTAR and shortest is not None:
                    self.assertEqual(body["metrics"]["path_length"], shortest, context)

                # what comes back over HTTP is exactly what the algorithm produced
                self.assertEqual(
                    [(c["row"], c["col"]) for c in body["path"]], [tuple(c) for c in direct.path], context
                )
                self.assertEqual(
                    [(e["step"], e["node"]["row"], e["node"]["col"], e["g"], e["h"], e["f"]) for e in merged_events(body)],
                    [(e.step, e.node.row, e.node.col, e.g, e.h, e.f) for e in direct.events],
                    context,
                )
                self.assertEqual(
                    {e["step"] for e in body["open_events"]}, {e.step for e in direct.open_events}, context
                )
                for event in merged_events(body):
                    self.assertEqual(
                        event["h"],
                        manhattan_distance(
                            type(problem.start)(event["node"]["row"], event["node"]["col"]), problem.end
                        ),
                    )


if __name__ == "__main__":
    import unittest

    unittest.main()
