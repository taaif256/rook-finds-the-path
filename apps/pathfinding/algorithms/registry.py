"""Look up an algorithm by its API identifier."""

from __future__ import annotations

from collections.abc import Callable, Mapping
from types import MappingProxyType

from .astar import a_star_search
from .greedy_best_first import greedy_best_first_search
from .problem import SearchProblem
from .result import AlgorithmId, SearchResult

SearchAlgorithm = Callable[[SearchProblem], SearchResult]

ALGORITHMS: Mapping[AlgorithmId, SearchAlgorithm] = MappingProxyType(
    {
        AlgorithmId.GBFS: greedy_best_first_search,
        AlgorithmId.ASTAR: a_star_search,
    }
)


class UnknownAlgorithmError(ValueError):
    """Raised for an algorithm identifier that is not registered."""


def get_algorithm(algorithm_id: str) -> SearchAlgorithm:
    try:
        return ALGORITHMS[AlgorithmId(algorithm_id)]
    except ValueError:
        valid = ", ".join(item.value for item in AlgorithmId)
        raise UnknownAlgorithmError(
            f"Unknown algorithm {algorithm_id!r}. Valid algorithms: {valid}."
        ) from None
