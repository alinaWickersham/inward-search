import os

import psycopg
import pytest
from fastapi.testclient import TestClient

from tests.conftest import FakeModel, make_listing
from threshold.api import app as api
from threshold.corpus import load_listings
from threshold.retrieval import cli, embed, store
from threshold.retrieval.store import Hit

LISTINGS = [
    make_listing("L1", "Pine Hollow", summary="Forest walking."),
    make_listing("L2", "Ocean Hermitage", summary="Sea cliffs.", tradition="yogic"),
]


class RecordingSearch:
    """A search function that returns fixed hits and remembers its calls."""

    def __init__(self, hits: list[Hit]) -> None:
        self.hits = hits
        self.calls: list[tuple[str, int]] = []

    def __call__(self, query: str, k: int) -> list[Hit]:
        self.calls.append((query, k))
        return self.hits[:k]


@pytest.fixture
def recorder() -> RecordingSearch:
    return RecordingSearch([Hit(listing_id="L2", score=0.9), Hit(listing_id="L1", score=0.25)])


@pytest.fixture
def client(recorder: RecordingSearch) -> TestClient:
    return TestClient(api.create_app(recorder, LISTINGS, "test-model"))


def test_search_returns_ranked_cards(client: TestClient, recorder: RecordingSearch) -> None:
    response = client.post("/api/search", json={"query": "  sea  ", "k": 2})
    assert response.status_code == 200
    body = response.json()
    assert recorder.calls == [("sea", 2)]
    assert (body["query"], body["strategy"], body["model"]) == ("sea", "embedding", "test-model")
    assert [(r["rank"], r["score"], r["listing"]["id"]) for r in body["results"]] == [
        (1, 0.9, "L2"),
        (2, 0.25, "L1"),
    ]
    assert body["results"][0]["listing"] == {
        "id": "L2",
        "name": "Ocean Hermitage",
        "location": "Invented Valley",
        "summary": "Sea cliffs.",
        "dimensions": {**LISTINGS[1].dimensions.model_dump(mode="json")},
        "synthetic": True,
    }


def test_search_defaults_k_to_ten(client: TestClient, recorder: RecordingSearch) -> None:
    client.post("/api/search", json={"query": "sea"})
    assert recorder.calls == [("sea", 10)]


def test_empty_results_are_a_valid_response() -> None:
    client = TestClient(api.create_app(RecordingSearch([]), LISTINGS, "test-model"))
    assert client.post("/api/search", json={"query": "sea"}).json()["results"] == []


@pytest.mark.parametrize(
    "body",
    [
        {},
        {"query": "sea", "k": 0},
        {"query": "sea", "k": api.MAX_K + 1},
        {"query": "x" * (api.MAX_QUERY_LENGTH + 1)},
        {"query": 42},
    ],
)
def test_invalid_requests_are_rejected_before_search(
    client: TestClient, recorder: RecordingSearch, body: dict
) -> None:
    assert client.post("/api/search", json=body).status_code == 422
    assert recorder.calls == []


def test_whitespace_query_is_rejected_with_a_readable_detail(
    client: TestClient, recorder: RecordingSearch
) -> None:
    response = client.post("/api/search", json={"query": " \n\t "})
    assert (response.status_code, response.json()) == (422, {"detail": "query is empty"})
    assert recorder.calls == []


def test_longest_allowed_query_is_accepted(client: TestClient) -> None:
    response = client.post("/api/search", json={"query": "x" * api.MAX_QUERY_LENGTH})
    assert response.status_code == 200


def test_search_is_not_available_as_get(client: TestClient) -> None:
    # The query must never travel in a URL, where access logs would keep it.
    # GET falls through to the static mount, which has no such file.
    assert client.get("/api/search", params={"query": "sea"}).status_code == 404


def test_frontend_is_served_at_the_root(client: TestClient) -> None:
    page = client.get("/")
    assert page.status_code == 200
    assert "Every listing here is synthetic" in page.text
    assert client.get("/style.css").status_code == 200


@pytest.fixture
def indexed_corpus(db: psycopg.Connection) -> psycopg.Connection:
    cli.run_index(db, FakeModel(), load_listings())
    return db


def test_build_app_returns_what_the_store_ranks(indexed_corpus: psycopg.Connection) -> None:
    query = "somewhere quiet where nobody asks me about work"
    client = TestClient(api.build_app(FakeModel(), os.environ["TEST_DATABASE_URL"]))
    body = client.post("/api/search", json={"query": query, "k": 5}).json()
    expected = store.search(indexed_corpus, embed.embed_query(FakeModel(), query), k=5)
    assert body["model"] == embed.MODEL_NAME
    assert [(r["listing"]["id"], r["score"]) for r in body["results"]] == [
        (hit.listing_id, hit.score) for hit in expected
    ]


def test_build_app_refuses_an_index_from_another_model(db: psycopg.Connection) -> None:
    listings = load_listings()
    vectors = embed.embed_listings(FakeModel(), listings)
    store.rebuild_index(db, "another-model", [item.id for item in listings], vectors)
    with pytest.raises(RuntimeError, match="different model"):
        api.build_app(FakeModel(), os.environ["TEST_DATABASE_URL"])


def test_build_app_refuses_an_index_that_does_not_match_the_corpus(db: psycopg.Connection) -> None:
    cli.run_index(db, FakeModel(), load_listings()[:5])
    with pytest.raises(RuntimeError, match="does not match the corpus"):
        api.build_app(FakeModel(), os.environ["TEST_DATABASE_URL"])


def test_production_app_uses_the_configured_database(
    indexed_corpus: psycopg.Connection, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(embed, "load_model", FakeModel)
    monkeypatch.setenv("DATABASE_URL", os.environ["TEST_DATABASE_URL"])
    client = TestClient(api.production_app())
    assert client.post("/api/search", json={"query": "silence"}).status_code == 200
