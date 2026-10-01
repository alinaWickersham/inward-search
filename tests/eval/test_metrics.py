import math
from collections.abc import Callable

import pytest

from threshold.eval import metrics

RANKED = ["a", "b", "c", "d", "e"]


@pytest.mark.parametrize(("k", "expected"), [(1, 0.0), (2, 1 / 3), (4, 1 / 3), (5, 2 / 3)])
def test_recall_at_k(k: int, expected: float) -> None:
    # "x" is relevant but never retrieved, so recall can never reach 1.
    assert metrics.recall_at_k(RANKED, {"b", "e", "x"}, k) == pytest.approx(expected)


def test_recall_with_k_past_the_ranking_counts_what_is_there() -> None:
    assert metrics.recall_at_k(["a"], {"a", "b"}, k=10) == pytest.approx(0.5)


def test_reciprocal_rank_uses_the_first_relevant_hit() -> None:
    assert metrics.reciprocal_rank(RANKED, {"c", "e"}) == pytest.approx(1 / 3)


def test_reciprocal_rank_is_zero_when_nothing_relevant_is_ranked() -> None:
    assert metrics.reciprocal_rank(RANKED, {"z"}) == 0.0


def test_mean_reciprocal_rank_averages_over_queries() -> None:
    runs = [(["a", "b"], {"a"}), (["a", "b"], {"b"}), (["a", "b"], {"z"})]
    assert metrics.mean_reciprocal_rank(runs) == pytest.approx((1 + 1 / 2 + 0) / 3)


def test_ndcg_hand_computed() -> None:
    # DCG  = 0/log2(2) + 2/log2(3) + 1/log2(4)           = 1.76186
    # IDCG = 2/log2(2) + 2/log2(3) + 1/log2(4) (2, 2, 1)  = 3.76186
    relevance = {"b": 2, "c": 1, "x": 2}
    expected = (2 / math.log2(3) + 0.5) / (2 + 2 / math.log2(3) + 0.5)
    assert expected == pytest.approx(0.46835, abs=1e-5)
    assert metrics.ndcg_at_k(["a", "b", "c"], relevance, k=3) == pytest.approx(expected)


def test_ndcg_is_one_for_the_ideal_ranking() -> None:
    assert metrics.ndcg_at_k(["x", "b", "c"], {"b": 2, "c": 1, "x": 2}, k=3) == pytest.approx(1.0)


def test_ndcg_only_looks_at_the_top_k() -> None:
    assert metrics.ndcg_at_k(["z", "a"], {"a": 1}, k=1) == 0.0
    # At k=2 the hit at rank 2 counts: (1/log2(3)) / (1/log2(2)).
    assert metrics.ndcg_at_k(["z", "a"], {"a": 1}, k=2) == pytest.approx(1 / math.log2(3))


@pytest.mark.parametrize(
    "call",
    [
        lambda: metrics.recall_at_k(RANKED, set(), 5),
        lambda: metrics.recall_at_k(RANKED, {"a"}, 0),
        lambda: metrics.recall_at_k(["a", "a"], {"a"}, 2),
        lambda: metrics.reciprocal_rank(RANKED, set()),
        lambda: metrics.reciprocal_rank(["a", "a"], {"a"}),
        lambda: metrics.mean_reciprocal_rank([]),
        lambda: metrics.ndcg_at_k(RANKED, {}, 5),
        lambda: metrics.ndcg_at_k(RANKED, {"a": 0}, 5),
        lambda: metrics.ndcg_at_k(RANKED, {"a": 1}, 0),
        lambda: metrics.ndcg_at_k(["a", "a"], {"a": 1}, 2),
    ],
)
def test_undefined_inputs_raise(call: Callable[[], float]) -> None:
    with pytest.raises(ValueError):
        call()
