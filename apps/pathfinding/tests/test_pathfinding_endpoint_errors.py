"""POST /api/v1/pathfinding/run/: every way a request can be rejected."""

from .helpers import RUN_URL, SPEC_EXAMPLE, ApiTestCase, run_payload, without

MAX_BARRIERS = 2500


def cell(row, col):
    return {"row": row, "col": col}


class AlgorithmFieldTests(ApiTestCase):
    def test_missing_algorithm(self):
        self.assertRejected(self.run_request(without(run_payload(), "algorithm")), "algorithm")

    def test_unknown_algorithm_names_are_rejected_and_valid_ones_listed(self):
        for bad in ("dijkstra", "ASTAR", "a*", "", 5, ["astar"], {"id": "astar"}):
            with self.subTest(algorithm=bad):
                body = self.assertRejected(self.run_request(run_payload(algorithm=bad)), "algorithm")
                text = " ".join(body["errors"]["algorithm"])
                self.assertIn("gbfs", text)
                self.assertIn("astar", text)

    def test_null_algorithm(self):
        self.assertRejected(self.run_request(run_payload(algorithm=None)), "algorithm")


class GridFieldTests(ApiTestCase):
    def test_missing_grid(self):
        self.assertRejected(self.run_request(without(run_payload(), "grid")), "grid")

    def test_grid_must_be_an_object(self):
        for bad in (5, "10x10", [10, 10], None):
            with self.subTest(grid=bad):
                self.assertRejected(self.run_request(run_payload(grid=bad)), "grid")

    def test_missing_dimensions(self):
        self.assertRejected(self.run_request(run_payload(grid={"cols": 10})), "grid.rows")
        self.assertRejected(self.run_request(run_payload(grid={"rows": 10})), "grid.cols")
        self.assertRejected(self.run_request(run_payload(grid={})), "grid.rows", "grid.cols")

    def test_dimensions_out_of_range(self):
        for bad in (0, -1, 51, 1000, 10**30):
            with self.subTest(size=bad):
                body = self.assertRejected(self.run_request(run_payload(grid={"rows": bad, "cols": 10})), "grid.rows")
                self.assertIn("between 1 and 50", body["errors"]["grid.rows"][0])
                self.assertRejected(self.run_request(run_payload(grid={"rows": 10, "cols": bad})), "grid.cols")

    def test_dimensions_must_be_json_integers(self):
        for bad in ("10", 10.5, 10.0, True, False, None, [10], {"n": 10}):
            with self.subTest(size=bad):
                self.assertRejected(self.run_request(run_payload(grid={"rows": bad, "cols": 10})), "grid.rows")
                self.assertRejected(self.run_request(run_payload(grid={"rows": 10, "cols": bad})), "grid.cols")

    def test_both_dimensions_reported_together(self):
        self.assertRejected(self.run_request(run_payload(grid={"rows": 0, "cols": 99})), "grid.rows", "grid.cols")

    def test_out_of_range_size_is_reported_alongside_unrelated_errors(self):
        # Size is a field-level rule, so it does not wait for the grid rules to run.
        for bad in (0, 51):
            for dimension in ("rows", "cols"):
                with self.subTest(**{dimension: bad}):
                    grid = {"rows": 10, "cols": 10, dimension: bad}
                    self.assertRejected(
                        self.run_request(run_payload(grid=grid, algorithm="dijkstra")),
                        "algorithm",
                        f"grid.{dimension}",
                    )


class CoordinateShapeTests(ApiTestCase):
    def test_missing_start_and_end(self):
        self.assertRejected(self.run_request(without(run_payload(), "start")), "start")
        self.assertRejected(self.run_request(without(run_payload(), "end")), "end")

    def test_start_and_end_must_be_objects(self):
        for field in ("start", "end"):
            for bad in ([0, 0], "0,0", 5, None):
                with self.subTest(field=field, value=bad):
                    self.assertRejected(self.run_request(run_payload(**{field: bad})), field)

    def test_missing_row_or_col(self):
        for field in ("start", "end"):
            self.assertRejected(self.run_request(run_payload(**{field: {"col": 1}})), f"{field}.row")
            self.assertRejected(self.run_request(run_payload(**{field: {"row": 1}})), f"{field}.col")
            self.assertRejected(self.run_request(run_payload(**{field: {}})), f"{field}.row", f"{field}.col")

    def test_row_and_col_must_be_json_integers(self):
        for field in ("start", "end"):
            for bad in ("1", 1.5, 1.0, True, None, [1]):
                with self.subTest(field=field, value=bad):
                    self.assertRejected(self.run_request(run_payload(**{field: {"row": bad, "col": 1}})), f"{field}.row")
                    self.assertRejected(self.run_request(run_payload(**{field: {"row": 1, "col": bad}})), f"{field}.col")


class GridRuleTests(ApiTestCase):
    """Rules that depend on the grid, enforced once by SearchProblem."""

    def test_start_and_end_outside_the_grid(self):
        for field in ("start", "end"):
            for row, col in ((-1, 0), (0, -1), (10, 0), (0, 10), (99, 99), (10**30, 0)):
                with self.subTest(field=field, row=row, col=col):
                    body = self.assertRejected(self.run_request(run_payload(**{field: cell(row, col)})), field)
                    self.assertIn("outside the 10x10 grid", body["errors"][field][0])

    def test_start_and_end_on_the_edges_are_inside(self):
        for start, end in ((cell(0, 0), cell(9, 9)), (cell(0, 9), cell(9, 0)), (cell(9, 9), cell(0, 0))):
            with self.subTest(start=start, end=end):
                self.assertEqual(self.run_request(run_payload(start=start, end=end)).status_code, 200)

    def test_start_must_differ_from_end(self):
        body = self.assertRejected(self.run_request(run_payload(end=cell(0, 0))), "end")
        self.assertIn("different from start", body["errors"]["end"][0])

    def test_one_by_one_grid_is_rejected(self):
        payload = run_payload(grid={"rows": 1, "cols": 1}, start=cell(0, 0), end=cell(0, 0), barriers=[])
        self.assertRejected(self.run_request(payload), "end")

    def test_start_cannot_be_on_a_barrier(self):
        body = self.assertRejected(self.run_request(run_payload(start=cell(2, 3))), "start")
        self.assertIn("barrier", body["errors"]["start"][0])

    def test_end_cannot_be_on_a_barrier(self):
        body = self.assertRejected(self.run_request(run_payload(end=cell(3, 3))), "end")
        self.assertIn("barrier", body["errors"]["end"][0])


class BarrierFieldTests(ApiTestCase):
    def test_barriers_must_be_a_list(self):
        for bad in ({}, {"row": 1, "col": 1}, "x", 5, None):
            with self.subTest(barriers=bad):
                self.assertRejected(self.run_request(run_payload(barriers=bad)), "barriers")

    def test_each_barrier_must_be_an_object(self):
        self.assertRejected(self.run_request(run_payload(barriers=[[1, 2]])), "barriers.0")
        self.assertRejected(self.run_request(run_payload(barriers=[cell(1, 1), "x"])), "barriers.1")

    def test_malformed_barriers_are_reported_by_position(self):
        payload = run_payload(barriers=[{"row": "a", "col": 0}, cell(1, 1), {"row": 2}])
        self.assertRejected(self.run_request(payload), "barriers.0.row", "barriers.2.col")

    def test_barrier_outside_the_grid(self):
        for bad in (cell(-1, 0), cell(0, -1), cell(10, 0), cell(0, 10), cell(10**30, 0)):
            with self.subTest(barrier=bad):
                body = self.assertRejected(self.run_request(run_payload(barriers=[cell(1, 1), bad])), "barriers")
                self.assertIn("outside the 10x10 grid", body["errors"]["barriers"][0])

    def test_too_many_barrier_entries(self):
        body = self.assertRejected(self.run_request(run_payload(barriers=[cell(1, 1)] * (MAX_BARRIERS + 1))), "barriers")
        self.assertIn(str(MAX_BARRIERS), body["errors"]["barriers"][0])


class MovementFieldTests(ApiTestCase):
    def test_only_four_directional_movement_is_supported(self):
        for bad in ("diagonal", "eight_directional", "FOUR_DIRECTIONAL", "", 4, None):
            with self.subTest(movement=bad):
                self.assertRejected(self.run_request(run_payload(movement=bad)), "movement")

    def test_unsupported_movement_message_names_the_supported_value(self):
        body = self.assertRejected(self.run_request(run_payload(movement="diagonal")), "movement")
        self.assertIn("four_directional", body["errors"]["movement"][0])


class RequestBodyTests(ApiTestCase):
    def post_raw(self, data, content_type="application/json"):
        return self.client.post(RUN_URL, data, content_type=content_type)

    def test_body_must_be_a_json_object(self):
        for raw in ("[]", "5", '"text"', "true"):
            with self.subTest(body=raw):
                self.assertRejected(self.post_raw(raw), "non_field_errors")

    def test_null_body(self):
        self.assertRejected(self.post_raw("null"), "non_field_errors")

    def test_empty_body_reports_every_required_field(self):
        self.assertRejected(self.post_raw(""), "algorithm", "grid", "start", "end")
        self.assertRejected(self.post_raw("{}"), "algorithm", "grid", "start", "end")

    def test_malformed_json(self):
        body = self.assertRejected(self.post_raw("{not json"), status=400, message=None)
        self.assertIn("JSON", body["message"])

    def test_non_json_content_types_are_unsupported(self):
        for content_type in ("text/plain", "application/x-www-form-urlencoded", "application/xml"):
            with self.subTest(content_type=content_type):
                body = self.assertRejected(self.post_raw("algorithm=astar", content_type), status=415, message=None)
                self.assertIn(content_type, body["message"])

    def test_only_post_is_allowed(self):
        for method in ("get", "put", "patch", "delete"):
            with self.subTest(method=method):
                response = getattr(self.client, method)(RUN_URL)
                body = self.assertRejected(response, status=405, message=None)
                self.assertIn("not allowed", body["message"])
                self.assertIn("POST", response.headers["Allow"])


class ErrorReportingTests(ApiTestCase):
    def test_independent_problems_are_reported_together(self):
        payload = run_payload(algorithm="dijkstra", grid={"rows": 0, "cols": 10}, movement="diagonal")
        payload.pop("end")
        self.assertRejected(self.run_request(payload), "algorithm", "grid.rows", "movement", "end")

    def test_grid_rules_are_only_checked_once_the_request_is_well_formed(self):
        # start == end is a grid rule: it is not reported while the algorithm name is still wrong...
        broken = run_payload(algorithm="dijkstra", end=cell(0, 0))
        self.assertRejected(self.run_request(broken), "algorithm")
        # ...but shows up as soon as the shape is fixed.
        self.assertRejected(self.run_request(run_payload(end=cell(0, 0))), "end")

    def test_errors_do_not_leak_internals(self):
        for payload in (run_payload(algorithm=None), run_payload(grid=5), run_payload(start=cell(99, 99))):
            text = self.run_request(payload).content.decode()
            for leak in ("Traceback", "File \"", "rest_framework", "apps.pathfinding", "detail"):
                self.assertNotIn(leak, text)

    def test_error_responses_are_readable_by_the_angular_dev_server(self):
        response = self.client.post(
            RUN_URL, run_payload(algorithm="nope"), format="json", headers={"Origin": "http://localhost:4200"}
        )
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.headers.get("Access-Control-Allow-Origin"), "http://localhost:4200")

    def test_spec_example_is_not_mutated_by_these_tests(self):
        self.assertEqual(SPEC_EXAMPLE["algorithm"], "astar")
        self.assertEqual(len(SPEC_EXAMPLE["barriers"]), 3)


if __name__ == "__main__":
    import unittest

    unittest.main()
