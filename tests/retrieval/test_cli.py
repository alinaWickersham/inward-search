import os

import psycopg
import pytest

from tests.conftest import FakeModel, make_listing
from threshold.corpus import load_listings
from threshold.retrieval import cli, embed, store

LISTINGS = [
    make_listing("L1", "Pine Hollow", summary="forest walking silence"),
    make_listing("L2", "Ocean Hermitage", summary="sea cliffs solitude prayer"),
    make_listing("L3", "City Sangha", summary="evening sitting group talk"),
]


def test_run_index_stores_every_listing_under_the_model_name(
    db: psycopg.Connection, fake_model: FakeModel
) -> None:
    assert cli.run_index(db, fake_model, LISTINGS) == f"indexed 3 listings with {embed.MODEL_NAME}"
    assert store.indexed_model(db) == embed.MODEL_NAME
    assert db.execute("SELECT count(*) FROM listing_embedding").fetchone() == (3,)


def test_run_search_puts_the_matching_listing_first_with_full_score(
    db: psycopg.Connection, fake_model: FakeModel
) -> None:
    cli.run_index(db, fake_model, LISTINGS)
    # The query is the listing's own text, so the fake vectors are identical.
    output = cli.run_search(db, fake_model, LISTINGS, embed.listing_text(LISTINGS[1]), k=2)
    lines = output.splitlines()
    assert len(lines) == 2
    assert lines[0] == " 1  1.000  L2  Ocean Hermitage"
    assert lines[1].startswith(" 2  ")


def test_full_corpus_indexes_and_ranks_in_descending_score(
    db: psycopg.Connection, fake_model: FakeModel
) -> None:
    corpus = load_listings()
    cli.run_index(db, fake_model, corpus)
    hits = store.search(db, embed.embed_query(fake_model, "a quiet silent weekend alone"), k=10)
    assert len(hits) == 10
    assert {h.listing_id for h in hits} <= {item.id for item in corpus}
    scores = [h.score for h in hits]
    assert scores == sorted(scores, reverse=True)


def test_parse_args_search_defaults_k_to_ten() -> None:
    args = cli.parse_args(["search", "somewhere quiet"])
    assert (args.command, args.query, args.k) == ("search", "somewhere quiet", 10)


def test_parse_args_requires_a_command() -> None:
    with pytest.raises(SystemExit):
        cli.parse_args([])


def test_parse_args_search_requires_a_query() -> None:
    with pytest.raises(SystemExit):
        cli.parse_args(["search"])


def test_main_indexes_then_searches_the_corpus(
    db: psycopg.Connection, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    monkeypatch.setattr(embed, "load_model", FakeModel)
    monkeypatch.setenv("DATABASE_URL", os.environ["TEST_DATABASE_URL"])
    cli.main(["index"])
    expected = f"indexed {len(load_listings())} listings with {embed.MODEL_NAME}\n"
    assert capsys.readouterr().out == expected
    cli.main(["search", "silent retreat", "-k", "3"])
    assert len(capsys.readouterr().out.splitlines()) == 3
