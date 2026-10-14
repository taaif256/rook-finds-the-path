"""Looking algorithms up by their API identifier."""

import unittest

from apps.pathfinding.algorithms import (
    ALGORITHMS,
    AlgorithmId,
    UnknownAlgorithmError,
    a_star_search,
    get_algorithm,
    greedy_best_first_search,
)

from .helpers import make_problem


class RegistryTests(unittest.TestCase):
    def test_identifiers_match_the_api_contract(self):
        self.assertEqual({item.value for item in AlgorithmId}, {"gbfs", "astar"})

    def test_every_identifier_has_an_algorithm(self):
        self.assertEqual(set(ALGORITHMS), set(AlgorithmId))

    def test_lookup_by_string(self):
        self.assertIs(get_algorithm("astar"), a_star_search)
        self.assertIs(get_algorithm("gbfs"), greedy_best_first_search)

    def test_result_reports_the_algorithm_that_produced_it(self):
        problem = make_problem(3, 3, (0, 0), (2, 2))
        for algorithm_id in AlgorithmId:
            self.assertEqual(get_algorithm(algorithm_id.value)(problem).algorithm, algorithm_id)

    def test_unknown_algorithm_is_rejected_and_valid_names_are_listed(self):
        for bad in ("dijkstra", "ASTAR", "", "a*"):
            with self.subTest(name=bad):
                with self.assertRaises(UnknownAlgorithmError) as raised:
                    get_algorithm(bad)
                self.assertIn("astar", str(raised.exception))
                self.assertIn("gbfs", str(raised.exception))


if __name__ == "__main__":
    unittest.main()
