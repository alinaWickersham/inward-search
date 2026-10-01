from pathlib import Path

import pytest
from pydantic import ValidationError

from threshold.eval import gold
from threshold.eval.gold import GoldIntent, GoldQuery
from threshold.schema import Duration, TriageClass


def labelled(**overrides: object) -> GoldQuery:
    fields = {
        "id": "Q001",
        "text": "somewhere quiet",
        "triage": TriageClass.SEEKING,
        "pool": ["L001", "L002"],
        "judgements": {"L001": 1, "L002": 0},
    }
    return GoldQuery.model_validate({**fields, **overrides})


def test_complete_needs_triage_a_pool_and_every_judgement() -> None:
    assert labelled().complete
    assert not labelled(triage=None).complete
    assert not labelled(pool=[], judgements={}).complete
    assert not labelled(judgements={"L001": 1}).complete


def test_relevant_is_the_listings_judged_one() -> None:
    assert labelled(judgements={"L001": 1, "L002": 0}).relevant == {"L001"}


def test_judgement_outside_the_pool_is_rejected() -> None:
    with pytest.raises(ValidationError, match="not in the pool"):
        labelled(judgements={"L001": 1, "L999": 0})


def test_pool_may_not_repeat_a_listing() -> None:
    with pytest.raises(ValidationError, match="repeats"):
        labelled(pool=["L001", "L001"], judgements={})


@pytest.mark.parametrize("grade", [2, -1, "1"])
def test_judgements_are_binary(grade: object) -> None:
    with pytest.raises(ValidationError):
        labelled(judgements={"L001": grade})


@pytest.mark.parametrize("query_id", ["Q1", "q001", "Q0001", "../Q001", ""])
def test_malformed_ids_are_rejected(query_id: str) -> None:
    with pytest.raises(ValidationError):
        labelled(id=query_id)
    with pytest.raises(ValueError):
        gold.path_for(Path("/tmp"), query_id)


def test_intent_accepts_several_values_and_rejects_unknown_ones() -> None:
    intent = GoldIntent.model_validate({"duration": ["weekend", "week"]})
    assert intent.duration == [Duration.WEEKEND, Duration.WEEK]
    assert intent.social == []
    with pytest.raises(ValidationError):
        GoldIntent.model_validate({"duration": ["fortnight"]})


def test_save_then_load_round_trips(tmp_path: Path) -> None:
    query = labelled(intent=GoldIntent.model_validate({"speech": ["full_silence"]}))
    gold.save_query(tmp_path, query)
    assert gold.load_query(tmp_path, "Q001") == query
    assert list(tmp_path.iterdir()) == [tmp_path / "Q001.json"]


def test_load_gold_is_sorted_by_id(tmp_path: Path) -> None:
    for query_id in ["Q010", "Q002", "Q001"]:
        gold.save_query(tmp_path, labelled(id=query_id))
    assert [q.id for q in gold.load_gold(tmp_path)] == ["Q001", "Q002", "Q010"]


def test_next_query_id_follows_the_highest(tmp_path: Path) -> None:
    assert gold.next_query_id(tmp_path) == "Q001"
    gold.save_query(tmp_path, labelled(id="Q002"))
    gold.save_query(tmp_path, labelled(id="Q009"))
    assert gold.next_query_id(tmp_path) == "Q010"


def test_committed_gold_files_validate() -> None:
    queries = gold.load_gold()
    assert [q.id for q in queries] == [f"Q{n:03d}" for n in range(1, len(queries) + 1)]
