"""Heuristic, frontier, event recorder, path reconstruction and result helpers."""

import unittest

from apps.pathfinding.algorithms import AlgorithmId, Coordinate, EventKind, SearchResult, manhattan_distance
from apps.pathfinding.algorithms.events import EventRecorder
from apps.pathfinding.algorithms.frontier import PriorityFrontier
from apps.pathfinding.algorithms.path import reconstruct_path

C = Coordinate


class ManhattanDistanceTests(unittest.TestCase):
    def test_distance_is_sum_of_row_and_column_difference(self):
        self.assertEqual(manhattan_distance(C(0, 0), C(3, 4)), 7)

    def test_distance_to_self_is_zero(self):
        self.assertEqual(manhattan_distance(C(2, 2), C(2, 2)), 0)

    def test_distance_is_symmetric(self):
        self.assertEqual(manhattan_distance(C(5, 1), C(2, 8)), manhattan_distance(C(2, 8), C(5, 1)))

    def test_adjacent_cells_are_one_apart(self):
        self.assertEqual(manhattan_distance(C(4, 4), C(4, 5)), 1)

    def test_diagonal_neighbours_are_two_apart(self):
        self.assertEqual(manhattan_distance(C(0, 0), C(1, 1)), 2)


class PriorityFrontierTests(unittest.TestCase):
    def test_pops_lowest_f_first_then_lowest_h_then_oldest(self):
        frontier = PriorityFrontier()
        frontier.push(C(0, 0), f=5, h=3)  # A
        frontier.push(C(0, 1), f=5, h=2)  # B
        frontier.push(C(0, 2), f=4, h=4)  # C
        frontier.push(C(0, 3), f=5, h=2)  # D (same priority as B, discovered later)
        self.assertEqual([frontier.pop() for _ in range(4)], [C(0, 2), C(0, 1), C(0, 3), C(0, 0)])

    def test_len_and_truthiness(self):
        frontier = PriorityFrontier()
        self.assertFalse(frontier)
        self.assertEqual(len(frontier), 0)
        frontier.push(C(0, 0), 1, 1)
        self.assertTrue(frontier)
        self.assertEqual(len(frontier), 1)


class EventRecorderTests(unittest.TestCase):
    def test_steps_are_one_sequence_across_open_and_closed(self):
        recorder = EventRecorder()
        recorder.open(C(0, 0), 0, 2, 2)
        recorder.close(C(0, 0), 0, 2, 2)
        recorder.open(C(0, 1), 1, 1, 2)
        events = recorder.events
        self.assertEqual([e.step for e in events], [0, 1, 2])
        self.assertEqual([e.kind for e in events], [EventKind.OPEN, EventKind.CLOSED, EventKind.OPEN])

    def test_events_are_returned_as_an_immutable_snapshot(self):
        recorder = EventRecorder()
        recorder.open(C(0, 0), 0, 1, 1)
        snapshot = recorder.events
        recorder.close(C(0, 0), 0, 1, 1)
        self.assertEqual(len(snapshot), 1)
        self.assertIsInstance(snapshot, tuple)


class ReconstructPathTests(unittest.TestCase):
    def test_walks_parents_from_goal_back_to_start(self):
        parents = {C(0, 0): None, C(0, 1): C(0, 0), C(1, 1): C(0, 1), C(5, 5): C(0, 0)}
        self.assertEqual(reconstruct_path(parents, C(1, 1)), (C(0, 0), C(0, 1), C(1, 1)))

    def test_ignores_branches_that_are_not_on_the_goal_chain(self):
        parents = {C(0, 0): None, C(0, 1): C(0, 0), C(1, 0): C(0, 0)}
        self.assertEqual(reconstruct_path(parents, C(1, 0)), (C(0, 0), C(1, 0)))

    def test_goal_equal_to_start_gives_single_cell_path(self):
        self.assertEqual(reconstruct_path({C(2, 2): None}, C(2, 2)), (C(2, 2),))

    def test_broken_chain_is_reported(self):
        with self.assertRaisesRegex(ValueError, "No parent recorded"):
            reconstruct_path({C(0, 0): None, C(1, 1): C(9, 9)}, C(1, 1))

    def test_cycle_is_reported_instead_of_looping_forever(self):
        with self.assertRaisesRegex(ValueError, "cycle"):
            reconstruct_path({C(0, 0): C(0, 1), C(0, 1): C(0, 0)}, C(0, 0))


class SearchResultTests(unittest.TestCase):
    def test_empty_path_means_no_path_found_with_zero_metrics(self):
        result = SearchResult(AlgorithmId.ASTAR, (), ())
        self.assertFalse(result.path_found)
        self.assertEqual((result.path_length, result.path_cost, result.explored_nodes), (0, 0, 0))

    def test_path_length_counts_moves_not_cells(self):
        result = SearchResult(AlgorithmId.ASTAR, (C(0, 0), C(0, 1), C(0, 2)), ())
        self.assertTrue(result.path_found)
        self.assertEqual(result.path_length, 2)
        self.assertEqual(result.path_cost, 2)


if __name__ == "__main__":
    unittest.main()
