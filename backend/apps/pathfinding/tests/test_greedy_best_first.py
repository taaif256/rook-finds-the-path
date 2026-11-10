"""Greedy Best-First-specific behaviour. GBFS is *not* required to be optimal."""

import random
from collections import Counter

from apps.pathfinding.algorithms import (
    AlgorithmId,
    Coordinate,
    a_star_search,
    greedy_best_first_search,
)

from .helpers import SearchAssertions, bfs_search, make_problem, parse_grid, random_problem

C = Coordinate


def summarize(result):
    return [(e.kind.value, tuple(e.node), e.g, e.h, e.f) for e in result.events]


class GreedyPathTests(SearchAssertions):
    def test_finds_a_valid_path_on_an_open_grid(self):
        problem = make_problem(5, 5, (0, 0), (4, 4))
        result = greedy_best_first_search(problem)
        self.assertValidPath(problem, result)
        self.assertEqual(result.algorithm, AlgorithmId.GBFS)

    def test_finds_a_valid_path_around_a_wall(self):
        problem = parse_grid("S.#E\n..#.\n..#.\n....")
        result = greedy_best_first_search(problem)
        self.assertValidPath(problem, result)
        self.assertTrue(result.path_found)

    def test_finds_a_path_exactly_when_one_exists(self):
        rng = random.Random(99)
        for _ in range(800):
            problem = random_problem(rng)
            result = greedy_best_first_search(problem)
            expected, _ = bfs_search(problem)
            with self.subTest(problem=problem):
                self.assertEqual(result.path_found, expected is not None)
                self.assertValidPath(problem, result)

    def test_is_not_guaranteed_to_be_shortest(self):
        """Documents the limitation the UI must explain; it is not a claim about every grid.

        Greedy heads straight along the top row toward the end, which looks closest,
        then has to loop around the barrier. A* pays attention to cost so far and
        takes the shorter route underneath.
        """
        problem = parse_grid(
            """
            ....S
            E#...
            """
        )
        greedy = greedy_best_first_search(problem)
        optimal = a_star_search(problem)
        self.assertValidPath(problem, greedy)
        self.assertValidPath(problem, optimal)
        self.assertEqual(optimal.path_length, 5)
        self.assertGreater(greedy.path_length, optimal.path_length)


class GreedyBookkeepingTests(SearchAssertions):
    def test_f_equals_h_on_every_event(self):
        result = greedy_best_first_search(parse_grid("S...\n.##.\n...E"))
        for event in result.events:
            self.assertEqual(event.f, event.h)

    def test_each_node_is_opened_and_closed_at_most_once(self):
        problem = parse_grid("S..#.\n.#...\n...#E\n.#...")
        result = greedy_best_first_search(problem)
        self.assertTrue(all(count == 1 for count in Counter(e.node for e in result.open_events).values()))
        self.assertTrue(all(count == 1 for count in Counter(e.node for e in result.closed_events).values()))

    def test_exact_event_sequence_on_a_two_by_two_grid(self):
        result = greedy_best_first_search(make_problem(2, 2, (0, 0), (1, 1)))
        self.assertEqual(
            summarize(result),
            [
                ("open", (0, 0), 0, 2, 2),
                ("closed", (0, 0), 0, 2, 2),
                ("open", (1, 0), 1, 1, 1),
                ("open", (0, 1), 1, 1, 1),
                ("closed", (1, 0), 1, 1, 1),
                ("open", (1, 1), 2, 0, 0),
                ("closed", (1, 1), 2, 0, 0),
            ],
        )
        self.assertEqual(result.path, (C(0, 0), C(1, 0), C(1, 1)))

    def test_expands_the_node_that_looks_closest_to_the_goal(self):
        # From the start, "right" (h=1) must be explored before "down" (h=3) on this open row.
        result = greedy_best_first_search(make_problem(3, 3, (0, 0), (0, 2)))
        explored = [tuple(e.node) for e in result.closed_events]
        self.assertEqual(explored[:3], [(0, 0), (0, 1), (0, 2)])


if __name__ == "__main__":
    import unittest

    unittest.main()
