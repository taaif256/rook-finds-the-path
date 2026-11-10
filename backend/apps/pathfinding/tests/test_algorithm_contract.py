"""Behaviour every algorithm must share, run against each registered algorithm."""

import itertools
import random

from apps.pathfinding.algorithms import ALGORITHMS, AlgorithmId, Coordinate, EventKind

from .helpers import SearchAssertions, bfs_search, make_problem, parse_grid, random_problem

C = Coordinate


class AlgorithmContractTests(SearchAssertions):
    """Each test runs once per algorithm (see ``each_algorithm``)."""

    def each_algorithm(self):
        for algorithm_id, algorithm in ALGORITHMS.items():
            with self.subTest(algorithm=algorithm_id.value):
                yield algorithm_id, algorithm

    def check(self, problem, *, found):
        """Run every algorithm on ``problem`` and apply the shared assertions."""
        results = {}
        for algorithm_id, algorithm in self.each_algorithm():
            result = algorithm(problem)
            self.assertEqual(result.algorithm, algorithm_id)
            self.assertEqual(result.path_found, found)
            self.assertValidPath(problem, result)
            self.assertEventInvariants(problem, result)
            results[algorithm_id] = result
        return results

    # --- routes -------------------------------------------------------------

    def test_clear_unobstructed_route(self):
        self.check(make_problem(5, 5, (0, 0), (4, 4)), found=True)

    def test_route_requiring_a_detour(self):
        self.check(parse_grid("S.#E\n..#.\n..#.\n...."), found=True)

    def test_empty_barrier_list(self):
        self.check(make_problem(4, 4, (0, 0), (3, 3), []), found=True)

    def test_start_and_end_adjacent(self):
        for result in self.check(make_problem(3, 3, (1, 1), (1, 2)), found=True).values():
            self.assertEqual(result.path_length, 1)

    def test_start_and_end_at_every_pair_of_corners(self):
        corners = [C(0, 0), C(0, 5), C(3, 0), C(3, 5)]
        for start, end in itertools.permutations(corners, 2):
            with self.subTest(start=tuple(start), end=tuple(end)):
                self.check(make_problem(4, 6, start, end), found=True)

    def test_start_and_end_on_opposite_edges_with_barriers(self):
        problem = parse_grid(
            """
            .S...
            .###.
            .#...
            .#.#.
            ...E.
            """
        )
        self.check(problem, found=True)

    def test_largest_supported_grid_corner_to_corner(self):
        problem = make_problem(50, 50, (0, 0), (49, 49))
        results = self.check(problem, found=True)
        self.assertEqual(results[AlgorithmId.ASTAR].path_length, 98)

    # --- degenerate grids ---------------------------------------------------

    def test_single_row_grid(self):
        results = self.check(make_problem(1, 6, (0, 0), (0, 5)), found=True)
        self.assertEqual({r.path_length for r in results.values()}, {5})

    def test_single_column_grid(self):
        results = self.check(make_problem(6, 1, (5, 0), (0, 0)), found=True)
        self.assertEqual({r.path_length for r in results.values()}, {5})

    def test_single_row_grid_blocked_by_a_barrier(self):
        results = self.check(parse_grid("S.#.E"), found=False)
        self.assertEqual({r.explored_nodes for r in results.values()}, {2})

    def test_single_column_grid_blocked_by_a_barrier(self):
        self.check(parse_grid("S\n.\n#\nE"), found=False)

    # --- no path ------------------------------------------------------------

    def test_completely_blocked_route_reports_no_path(self):
        problem = parse_grid(
            """
            S.#..
            ..#..
            ..#.E
            """
        )
        _, reachable = bfs_search(problem)
        self.assertEqual(len(reachable), 6)
        for result in self.check(problem, found=False).values():
            self.assertEqual(result.path, ())
            self.assertEqual(result.path_length, 0)
            self.assertEqual(result.path_cost, 0)
            # the search is exhaustive: it explores the whole reachable region, then stops
            self.assertEqual({e.node for e in result.closed_events}, reachable)

    def test_barriers_surrounding_the_start(self):
        problem = parse_grid(
            """
            .#...
            #S#..
            .#..E
            """
        )
        for result in self.check(problem, found=False).values():
            self.assertEqual(result.explored_nodes, 1)
            self.assertEqual([(e.kind, e.node) for e in result.events],
                             [(EventKind.OPEN, problem.start), (EventKind.CLOSED, problem.start)])

    def test_end_enclosed_by_barriers(self):
        problem = parse_grid(
            """
            S....
            .....
            ..#..
            .#E#.
            ..#..
            """
        )
        for result in self.check(problem, found=False).values():
            self.assertNotIn(problem.end, {e.node for e in result.events})

    # --- events -------------------------------------------------------------

    def test_events_contain_open_and_closed_states_in_a_single_ordered_sequence(self):
        problem = parse_grid("S...\n.##.\n...E")
        for _, algorithm in self.each_algorithm():
            result = algorithm(problem)
            kinds = {e.kind for e in result.events}
            self.assertEqual(kinds, {EventKind.OPEN, EventKind.CLOSED})
            merged = sorted(result.open_events + result.closed_events, key=lambda e: e.step)
            self.assertEqual(merged, list(result.events))

    def test_search_never_touches_barriers_or_cells_outside_the_grid(self):
        problem = parse_grid("S#.#.\n.#.#.\n.#.#E\n.....")
        for _, algorithm in self.each_algorithm():
            for event in algorithm(problem).events:
                self.assertTrue(problem.in_bounds(event.node))
                self.assertNotIn(event.node, problem.barriers)

    def test_every_node_on_the_path_was_explored(self):
        problem = parse_grid("S...\n.##.\n...E")
        for _, algorithm in self.each_algorithm():
            result = algorithm(problem)
            explored = {e.node for e in result.closed_events}
            self.assertTrue(set(result.path) <= explored)

    def test_searches_are_deterministic(self):
        problem = parse_grid("S..#.\n.#...\n...#E\n.#...")
        for _, algorithm in self.each_algorithm():
            self.assertEqual(algorithm(problem), algorithm(problem))

    def test_running_a_search_does_not_modify_the_problem(self):
        problem = parse_grid("S..#.\n.#...\n...#E\n.#...")
        before = (problem.rows, problem.cols, problem.start, problem.end, problem.barriers)
        for _, algorithm in self.each_algorithm():
            algorithm(problem)
        self.assertEqual(before, (problem.rows, problem.cols, problem.start, problem.end, problem.barriers))

    # --- randomized cross-check against an independent oracle ---------------

    def test_random_grids_agree_with_breadth_first_search(self):
        rng = random.Random(31337)
        for _ in range(500):
            problem = random_problem(rng)
            shortest, reachable = bfs_search(problem)
            for algorithm_id, algorithm in ALGORITHMS.items():
                result = algorithm(problem)
                context = f"{algorithm_id.value} on {problem}"
                self.assertEqual(result.path_found, shortest is not None, context)
                self.assertValidPath(problem, result)
                self.assertEventInvariants(problem, result)
                if shortest is None:
                    self.assertEqual({e.node for e in result.closed_events}, reachable, context)


if __name__ == "__main__":
    import unittest

    unittest.main()
