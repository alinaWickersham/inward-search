import math

import numpy as np
import psycopg
import pytest

from threshold.retrieval import store


def vectors(*rows: list[float]) -> np.ndarray:
    return np.array(rows, dtype=np.float32)


@pytest.fixture
def four_listings(db: psycopg.Connection) -> psycopg.Connection:
    # Against the query [1, 0, 0]: cosines are 1, 1/sqrt(2), 0, -1.
    store.rebuild_index(
        db,
        "test-model",
        ["L_A", "L_B", "L_C", "L_D"],
        vectors([1, 0, 0], [1, 1, 0], [0, 1, 0], [-1, 0, 0]),
    )
    return db


def test_search_ranks_by_cosine_similarity(four_listings: psycopg.Connection) -> None:
    hits = store.search(four_listings, np.array([1, 0, 0], dtype=np.float32), k=4)
    assert [h.listing_id for h in hits] == ["L_A", "L_B", "L_C", "L_D"]
    assert [h.score for h in hits] == pytest.approx([1.0, 1 / math.sqrt(2), 0.0, -1.0], abs=1e-6)


def test_search_ignores_query_length(four_listings: psycopg.Connection) -> None:
    # Cosine, not dot product: scaling the query must not change any score.
    hits = store.search(four_listings, np.array([5, 0, 0], dtype=np.float32), k=4)
    assert [h.score for h in hits] == pytest.approx([1.0, 1 / math.sqrt(2), 0.0, -1.0], abs=1e-6)


def test_search_returns_only_top_k(four_listings: psycopg.Connection) -> None:
    hits = store.search(four_listings, np.array([0, 1, 0], dtype=np.float32), k=2)
    # Against [0, 1, 0]: L_C is 1, L_B is 1/sqrt(2), the other two are 0.
    assert [h.listing_id for h in hits] == ["L_C", "L_B"]


def test_search_with_k_above_corpus_size_returns_everything(
    four_listings: psycopg.Connection,
) -> None:
    assert len(store.search(four_listings, np.array([1, 0, 0], dtype=np.float32), k=50)) == 4


def test_equal_scores_are_ordered_by_listing_id(db: psycopg.Connection) -> None:
    store.rebuild_index(db, "test-model", ["L9", "L2", "L5"], vectors([0, 1], [0, 1], [0, 1]))
    hits = store.search(db, np.array([0, 1], dtype=np.float32), k=3)
    assert [h.listing_id for h in hits] == ["L2", "L5", "L9"]


def test_search_rejects_k_below_one(four_listings: psycopg.Connection) -> None:
    with pytest.raises(ValueError):
        store.search(four_listings, np.array([1, 0, 0], dtype=np.float32), k=0)


def test_rebuild_replaces_rows_and_width(four_listings: psycopg.Connection) -> None:
    store.rebuild_index(four_listings, "other-model", ["L_Z"], vectors([0, 1]))
    hits = store.search(four_listings, np.array([0, 1], dtype=np.float32), k=10)
    assert [h.listing_id for h in hits] == ["L_Z"]
    assert store.indexed_model(four_listings) == "other-model"


def test_rebuild_rejects_mismatched_lengths_and_keeps_old_index(
    four_listings: psycopg.Connection,
) -> None:
    with pytest.raises(ValueError):
        store.rebuild_index(four_listings, "test-model", ["L_X", "L_Y"], vectors([1, 0, 0]))
    assert len(store.search(four_listings, np.array([1, 0, 0], dtype=np.float32), k=10)) == 4


def test_indexed_model_names_the_model(four_listings: psycopg.Connection) -> None:
    assert store.indexed_model(four_listings) == "test-model"


def test_indexed_model_refuses_a_mixed_index(four_listings: psycopg.Connection) -> None:
    four_listings.execute(
        "INSERT INTO listing_embedding VALUES ('L_E', 'second-model', %s)",
        (np.array([0, 0, 1], dtype=np.float32),),
    )
    with pytest.raises(RuntimeError):
        store.indexed_model(four_listings)


def test_database_url_reads_environment(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("DATABASE_URL", "postgresql://example/db")
    assert store.database_url() == "postgresql://example/db"
    monkeypatch.delenv("DATABASE_URL")
    assert store.database_url() == store.DEFAULT_DATABASE_URL


def test_indexed_listing_ids(four_listings: psycopg.Connection) -> None:
    assert store.indexed_listing_ids(four_listings) == {"L_A", "L_B", "L_C", "L_D"}
