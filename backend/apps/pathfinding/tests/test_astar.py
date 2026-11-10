"""A*-specific behaviour: optimality, cost bookkeeping and updating better routes."""

import random
from collections import Counter

from apps.pathfinding.algorithms import AlgorithmId, Coordinate, EventKind, a_star_search

from .helpers import SearchAssertions, bfs_search, make_problem, parse_grid, random_problem

C = Coordinate


def summarize(result):
    return [(e.kind.value, tuple(e.node), e.g, e.h, e.f) for e in result.events]


class AStarOptimalityTests(SearchAssertions):
    def test_open_grid_path_length_equals_manhattan_distance(self):
        problem = make_problem(5, 5, (0, 0), (4, 4))
        result = a_star_search(problem)
        self.assertValidPath(problem, result)
        self.assertEqual(result.path_length, 8)
        self.assertEqual(result.algorithm, AlgorithmId.ASTAR)

    def test_detour_around_a_wall_is_the_shortest_possible(self):
        problem = parse_grid(
            """
            S.#E
            ..#.
            ..#.
            ....
            """
        )
        result = a_star_search(problem)
        self.assertValidPath(problem, result)
        # down 3, across 3, up 3: the straight-line distance is only 3
        self.assertEqual(result.path_length, 9)
        self.assertEqual(result.path_length, bfs_search(problem)[0])

    def test_takes_the_gap_in_a_wall_even_when_it_is_far_away(self):
        problem = parse_grid(
            """
            S.#..
            ..#..
            ..#..
            .....
            ....E
            """
        )
        result = a_star_search(problem)
        self.assertValidPath(problem, result)
        self.assertEqual(result.path_length, bfs_search(problem)[0])

    def test_matches_bfs_shortest_path_on_many_random_grids(self):
        rng = random.Random(2024)
        for _ in range(800):
            problem = random_problem(rng)
            result = a_star_search(problem)
            expected, _ = bfs_search(problem)
            with self.subTest(problem=problem):
                self.assertEqual(result.path_found, expected is not None)
                if expected is not None:
                    self.assertEqual(result.path_length, expected)
                    self.assertValidPath(problem, result)

    def test_matches_bfs_on_the_largest_grid(self):
        rng = random.Random(7)
        cells = [C(r, c) for r in range(50) for c in range(50)]
        barriers = frozenset(
            cell for cell in cells if cell not in (C(0, 0), C(49, 49)) and rng.random() < 0.25
        )
        problem = make_problem(50, 50, (0, 0), (49, 49), barriers)
        result = a_star_search(problem)
        expected, _ = bfs_search(problem)
        self.assertEqual(result.path_found, expected is not None)
        if expected is not None:
            self.assertEqual(result.path_length, expected)
            self.assertValidPath(problem, result)


class AStarBookkeepingTests(SearchAssertions):
    def test_f_is_g_plus_h_on_every_event(self):
        result = a_star_search(parse_grid("S...\n.##.\n...E"))
        for event in result.events:
            self.assertEqual(event.f, event.g + event.h)

    def test_goal_g_score_equals_path_cost(self):
        problem = parse_grid("S.#E\n..#.\n..#.\n....")
        result = a_star_search(problem)
        self.assertEqual(result.closed_events[-1].g, result.path_cost)

    def test_exact_event_sequence_on_a_two_by_two_grid(self):
        # Up, down, left, right neighbour order and (f, h, age) tie-breaking, spelled out.
        result = a_star_search(make_problem(2, 2, (0, 0), (1, 1)))
        self.assertEqual(
            summarize(result),
            [
                ("open", (0, 0), 0, 2, 2),
                ("closed", (0, 0), 0, 2, 2),
                ("open", (1, 0), 1, 1, 2),
                ("open", (0, 1), 1, 1, 2),
                ("closed", (1, 0), 1, 1, 2),
                ("open", (1, 1), 2, 0, 2),
                ("closed", (1, 1), 2, 0, 2),
            ],
        )
        self.assertEqual(result.path, (C(0, 0), C(1, 0), C(1, 1)))

    def test_cheaper_route_to_an_open_node_updates_it_and_reopens_the_event(self):
        problem = parse_grid(
            """
            ....S
            E#...
            """
        )
        result = a_star_search(problem)
        opens_of_node = [e for e in result.events if e.kind is EventKind.OPEN and e.node == C(0, 2)]
        # First seen via the bottom row at g=4, then improved to g=2 through the top row.
        self.assertEqual([e.g for e in opens_of_node], [4, 2])
        self.assertLess(opens_of_node[0].step, opens_of_node[1].step)

        self.assertValidPath(problem, result)
        self.assertEqual(result.path, (C(0, 4), C(0, 3), C(0, 2), C(0, 1), C(0, 0), C(1, 0)))
        self.assertEqual(result.path_length, 5)
        self.assertEqual(result.path_length, bfs_search(problem)[0])
        self.assertEqual(Counter(e.node for e in result.closed_events)[C(0, 2)], 1)

    def test_events_satisfy_invariants_on_a_reopen_grid(self):
        problem = parse_grid("....S\nE#...")
        self.assertEventInvariants(problem, a_star_search(problem))


if __name__ == "__main__":
    import unittest

    unittest.main()
