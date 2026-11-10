"""SearchProblem: input validation and grid geometry."""

import unittest

from apps.pathfinding.algorithms import (
    MAX_GRID_SIZE,
    Coordinate,
    InvalidSearchProblemError,
    SearchProblem,
)

from .helpers import make_problem


class ValidProblemTests(unittest.TestCase):
    def test_plain_tuples_are_normalised_to_coordinates(self):
        problem = SearchProblem(3, 3, (0, 0), (2, 2), [(1, 1)])
        self.assertEqual(problem.start, Coordinate(0, 0))
        self.assertIsInstance(problem.start, Coordinate)
        self.assertEqual(problem.barriers, frozenset({Coordinate(1, 1)}))

    def test_empty_barrier_list_is_valid(self):
        self.assertEqual(SearchProblem(2, 2, (0, 0), (1, 1), []).barriers, frozenset())
        self.assertEqual(SearchProblem(2, 2, (0, 0), (1, 1)).barriers, frozenset())

    def test_duplicate_barriers_are_collapsed(self):
        problem = SearchProblem(3, 3, (0, 0), (2, 2), [(1, 1), (1, 1), (1, 1)])
        self.assertEqual(problem.barriers, frozenset({Coordinate(1, 1)}))

    def test_boundary_cells_are_valid(self):
        problem = SearchProblem(4, 6, (0, 0), (3, 5))
        self.assertEqual((problem.start, problem.end), (Coordinate(0, 0), Coordinate(3, 5)))

    def test_size_limits_are_inclusive(self):
        SearchProblem(1, 2, (0, 0), (0, 1))
        SearchProblem(MAX_GRID_SIZE, MAX_GRID_SIZE, (0, 0), (MAX_GRID_SIZE - 1, MAX_GRID_SIZE - 1))


class InvalidProblemTests(unittest.TestCase):
    def assertInvalid(self, field, *args):
        with self.assertRaises(InvalidSearchProblemError) as raised:
            SearchProblem(*args)
        self.assertEqual(raised.exception.field, field)
        return raised.exception

    def test_grid_size_out_of_range(self):
        for size in (0, -1, MAX_GRID_SIZE + 1):
            with self.subTest(size=size):
                self.assertInvalid("grid.rows", size, 5, (0, 0), (0, 1))
                self.assertInvalid("grid.cols", 5, size, (0, 0), (1, 0))

    def test_grid_size_must_be_an_integer(self):
        for bad in (2.0, "3", None, True):
            with self.subTest(value=bad):
                self.assertInvalid("grid.rows", bad, 3, (0, 0), (0, 1))

    def test_one_by_one_grid_has_no_room_for_distinct_start_and_end(self):
        self.assertInvalid("end", 1, 1, (0, 0), (0, 0))

    def test_start_and_end_out_of_bounds(self):
        for bad in ((-1, 0), (0, -1), (3, 0), (0, 3)):
            with self.subTest(coordinate=bad):
                self.assertInvalid("start", 3, 3, bad, (2, 2))
                self.assertInvalid("end", 3, 3, (0, 0), bad)

    def test_out_of_bounds_message_names_the_cell_and_grid(self):
        error = self.assertInvalid("start", 3, 4, (5, 5), (0, 0))
        self.assertIn("(5, 5)", error.message)
        self.assertIn("3x4", error.message)

    def test_barrier_out_of_bounds(self):
        for bad in ((-1, 0), (3, 0), (0, 3), (9, 9)):
            with self.subTest(coordinate=bad):
                self.assertInvalid("barriers", 3, 3, (0, 0), (2, 2), [(1, 1), bad])

    def test_start_equals_end(self):
        self.assertInvalid("end", 3, 3, (1, 1), (1, 1))

    def test_start_on_barrier(self):
        error = self.assertInvalid("start", 3, 3, (0, 0), (2, 2), [(0, 0)])
        self.assertIn("barrier", error.message)

    def test_end_on_barrier(self):
        error = self.assertInvalid("end", 3, 3, (0, 0), (2, 2), [(2, 2)])
        self.assertIn("barrier", error.message)

    def test_malformed_coordinates(self):
        for bad in (None, (1,), (1, 2, 3), ("a", "b"), (1.5, 2), (True, 0), 7):
            with self.subTest(value=bad):
                self.assertInvalid("start", 3, 3, bad, (2, 2))
                self.assertInvalid("barriers", 3, 3, (0, 0), (2, 2), [bad])

    def test_barriers_must_be_iterable(self):
        self.assertInvalid("barriers", 3, 3, (0, 0), (2, 2), None)
        self.assertInvalid("barriers", 3, 3, (0, 0), (2, 2), 5)

    def test_error_is_a_value_error_with_field_in_message(self):
        error = self.assertInvalid("end", 3, 3, (1, 1), (1, 1))
        self.assertIsInstance(error, ValueError)
        self.assertTrue(str(error).startswith("end:"))


class NeighbourTests(unittest.TestCase):
    def test_neighbours_in_up_down_left_right_order(self):
        problem = make_problem(3, 3, (0, 0), (2, 2))
        self.assertEqual(
            list(problem.neighbors(Coordinate(1, 1))),
            [Coordinate(0, 1), Coordinate(2, 1), Coordinate(1, 0), Coordinate(1, 2)],
        )

    def test_no_diagonal_moves(self):
        problem = make_problem(3, 3, (0, 0), (2, 2))
        self.assertNotIn(Coordinate(0, 0), problem.neighbors(Coordinate(1, 1)))

    def test_corner_has_two_neighbours(self):
        problem = make_problem(3, 3, (0, 0), (2, 2))
        self.assertEqual(list(problem.neighbors(Coordinate(0, 0))), [Coordinate(1, 0), Coordinate(0, 1)])

    def test_barriers_are_excluded(self):
        problem = make_problem(3, 3, (0, 0), (2, 2), [(0, 1), (1, 0)])
        self.assertEqual(list(problem.neighbors(Coordinate(0, 0))), [])

    def test_single_cell_row_has_only_horizontal_neighbours(self):
        problem = make_problem(1, 5, (0, 0), (0, 4))
        self.assertEqual(list(problem.neighbors(Coordinate(0, 2))), [Coordinate(0, 1), Coordinate(0, 3)])


if __name__ == "__main__":
    unittest.main()
