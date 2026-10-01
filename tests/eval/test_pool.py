import json
from pathlib import Path

import pytest

from tests.conftest import make_listing
from threshold.eval import pool
from threshold.eval.gold import GoldIntent, GoldQuery

LISTINGS = [
    make_listing("L1", "a", speech="full_silence", duration="weekend"),
    make_listing("L2", "b", speech="full_silence", duration="week"),
    make_listing("L3", "c", speech="dialogue", duration="weekend"),
    make_listing("L4", "d", speech="full_silence", duration="extended"),
    make_listing("L5", "e", speech="dialogue", duration="hours"),
]


def intent(**values: list[str]) -> GoldIntent:
    return GoldIntent.model_validate(values)


@pytest.mark.parametrize(
    ("constraints", "expected"),
    [
        ({"speech": ["full_silence"]}, {"L1", "L2", "L4"}),
        ({"speech": ["full_silence"], "duration": ["weekend", "week"]}, {"L1", "L2"}),
        ({"duration": ["hours"], "speech": ["full_silence"]}, set()),
        ({}, set()),
    ],
)
def test_matches_intent_requires_every_constrained_dimension(
    constraints: dict[str, list[str]], expected: set[str]
) -> None:
    gold_intent = intent(**constraints)
    assert {item.id for item in LISTINGS if pool.matches_intent(item, gold_intent)} == expected


def test_pool_is_embedding_top_plus_intent_matches_plus_partners() -> None:
    query = GoldQuery(id="Q001", text="silent weekend", intent=intent(duration=["week"]))
    result = pool.extend_pool(query, ["L5", "L3"], LISTINGS, {"L3": "L4", "L4": "L3"}, "m")
    # L5, L3 from embeddings; L2 matches the intent; L4 is L3's partner.
    assert sorted(result.pool) == ["L2", "L3", "L4", "L5"]
    assert result.pool_provenance.model_dump() == {"embedding_model": "m", "embedding_depth": 2}


def test_pool_order_is_a_seeded_shuffle_not_the_embedding_ranking() -> None:
    query = GoldQuery(id="Q001", text="x")
    ranking = [f"L{n:03d}" for n in range(1, 21)]
    first = pool.extend_pool(query, ranking, [], {}, "m").pool
    again = pool.extend_pool(query, ranking, [], {}, "m").pool
    assert first == again
    assert first != ranking
    other = pool.extend_pool(GoldQuery(id="Q002", text="x"), ranking, [], {}, "m").pool
    assert other != first


def test_extending_keeps_existing_members_order_and_judgements() -> None:
    query = GoldQuery(id="Q001", text="x", pool=["L3", "L1"], judgements={"L3": 1, "L1": 0})
    result = pool.extend_pool(query, ["L1", "L5"], LISTINGS, {}, "m")
    assert result.pool[:2] == ["L3", "L1"]
    assert result.pool[2:] == ["L5"]
    assert result.judgements == {"L3": 1, "L1": 0}


def test_partners_come_from_the_corpus_pair_field(tmp_path: Path) -> None:
    (tmp_path / "listings").mkdir()
    for lid, pair in [("L1", "pair00"), ("L2", "pair00"), ("L3", None)]:
        (tmp_path / "listings" / f"{lid}.json").write_text(json.dumps({"id": lid, "pair": pair}))
    assert pool.near_duplicate_partners(tmp_path) == {"L1": "L2", "L2": "L1"}


def test_a_pair_without_two_members_is_an_error(tmp_path: Path) -> None:
    (tmp_path / "listings").mkdir()
    (tmp_path / "listings" / "L1.json").write_text(json.dumps({"id": "L1", "pair": "pair00"}))
    with pytest.raises(ValueError, match="pair00 has 1 members"):
        pool.near_duplicate_partners(tmp_path)


def test_real_corpus_has_twelve_pairs() -> None:
    partners = pool.near_duplicate_partners()
    assert len(partners) == 24
    assert all(partners[partners[lid]] == lid for lid in partners)
