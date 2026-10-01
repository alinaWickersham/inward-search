"""
Ranking metrics for the strategy comparison.

Each function takes a ranking as a list of listing ids, best first, and
the gold labels for one query. Inputs that make a metric undefined (no
relevant listings, a ranking that repeats an id) raise instead of
returning 0, so a broken gold set cannot quietly lower a score.
"""

import math


def _check(ranked: list[str], k: int | None = None) -> None:
    if len(set(ranked)) != len(ranked):
        raise ValueError("ranking repeats a listing id")
    if k is not None and k < 1:
        raise ValueError("k must be at least 1")


def recall_at_k(ranked: list[str], relevant: set[str], k: int) -> float:
    """Fraction of the relevant listings that appear in the top k."""
    _check(ranked, k)
    if not relevant:
        raise ValueError("recall is undefined with no relevant listings")
    return len(set(ranked[:k]) & relevant) / len(relevant)


def reciprocal_rank(ranked: list[str], relevant: set[str]) -> float:
    """1 / rank of the first relevant listing, or 0 if none is ranked."""
    _check(ranked)
    if not relevant:
        raise ValueError("reciprocal rank is undefined with no relevant listings")
    for rank, listing_id in enumerate(ranked, start=1):
        if listing_id in relevant:
            return 1 / rank
    return 0.0


def mean_reciprocal_rank(runs: list[tuple[list[str], set[str]]]) -> float:
    """Mean of reciprocal_rank over (ranking, relevant) pairs, one per query."""
    if not runs:
        raise ValueError("MRR is undefined over zero queries")
    return sum(reciprocal_rank(ranked, relevant) for ranked, relevant in runs) / len(runs)


def _dcg(gains: list[int]) -> float:
    # Linear gain, log2(rank + 1) discount, ranks starting at 1.
    return sum(gain / math.log2(rank + 1) for rank, gain in enumerate(gains, start=1))


def ndcg_at_k(ranked: list[str], relevance: dict[str, int], k: int) -> float:
    """
    Normalised discounted cumulative gain over the top k.

    `relevance` maps listing id to a graded label; ids missing from it
    count as 0. The ideal ranking is the gold grades sorted descending.
    """
    _check(ranked, k)
    ideal = sorted(relevance.values(), reverse=True)[:k]
    if not any(grade > 0 for grade in ideal):
        raise ValueError("nDCG is undefined with no listing graded above 0")
    actual = [relevance.get(listing_id, 0) for listing_id in ranked[:k]]
    return _dcg(actual) / _dcg(ideal)
