import os
from pathlib import Path

import psycopg
import pytest
from fastapi.testclient import TestClient

from tests.conftest import FakeModel, make_listing
from threshold.api import label
from threshold.corpus import load_listings
from threshold.eval import gold
from threshold.eval.gold import GoldQuery
from threshold.retrieval import cli, embed

LISTINGS = [
    make_listing("L1", "Pine Hollow", speech="full_silence"),
    make_listing("L2", "Ocean Hermitage", speech="dialogue"),
    make_listing("L3", "City Sangha", speech="dialogue"),
]


class RecordingTop:
    def __init__(self, ids: list[str]) -> None:
        self.ids = ids
        self.calls: list[str] = []

    def __call__(self, text: str) -> list[str]:
        self.calls.append(text)
        return self.ids


@pytest.fixture
def top() -> RecordingTop:
    return RecordingTop(["L2"])


@pytest.fixture
def client(tmp_path: Path, top: RecordingTop) -> TestClient:
    gold.save_query(tmp_path, GoldQuery(id="Q001", text="somewhere silent"))
    app = label.create_label_app(top, "test-model", LISTINGS, {"L2": "L3", "L3": "L2"}, tmp_path)
    return TestClient(app)


def test_list_summarises_progress(client: TestClient) -> None:
    assert client.get("/api/gold").json() == [
        {
            "id": "Q001",
            "text": "somewhere silent",
            "triage_set": False,
            "pool_size": 0,
            "judged": 0,
            "complete": False,
        }
    ]


def test_add_query_assigns_the_next_id_and_saves(client: TestClient, tmp_path: Path) -> None:
    response = client.post("/api/gold", json={"text": "  a quiet week  "})
    assert response.status_code == 201
    assert (response.json()["id"], response.json()["text"]) == ("Q002", "a quiet week")
    assert gold.load_query(tmp_path, "Q002").text == "a quiet week"


@pytest.mark.parametrize("text", ["", "   "])
def test_add_query_rejects_empty_text(client: TestClient, text: str) -> None:
    assert client.post("/api/gold", json={"text": text}).status_code == 422


def test_get_query_handles_missing_and_malformed_ids(client: TestClient) -> None:
    assert client.get("/api/gold/Q001").json()["text"] == "somewhere silent"
    assert client.get("/api/gold/Q999").status_code == 404
    assert client.get("/api/gold/nope").status_code == 422


def test_build_pool_uses_the_query_text_and_saves(
    client: TestClient, top: RecordingTop, tmp_path: Path
) -> None:
    query = client.get("/api/gold/Q001").json()
    query["intent"]["speech"] = ["full_silence"]
    client.put("/api/gold/Q001", json=query)

    pooled = client.post("/api/gold/Q001/pool").json()
    assert top.calls == ["somewhere silent"]
    # L2 from embeddings, L3 as L2's partner, L1 from the intent.
    assert sorted(pooled["pool"]) == ["L1", "L2", "L3"]
    assert pooled["pool_provenance"] == {"embedding_model": "test-model", "embedding_depth": 1}
    assert gold.load_query(tmp_path, "Q001").pool == pooled["pool"]


def test_judging_every_pool_listing_with_triage_completes_a_query(
    client: TestClient, tmp_path: Path
) -> None:
    query = client.post("/api/gold/Q001/pool").json()
    query["triage"] = "seeking"
    query["judgements"] = {lid: 1 if lid == "L2" else 0 for lid in query["pool"]}
    assert client.put("/api/gold/Q001", json=query).status_code == 200
    saved = gold.load_query(tmp_path, "Q001")
    assert saved.complete
    assert saved.relevant == {"L2"}
    assert client.get("/api/gold").json()[0]["complete"] is True


def test_put_cannot_change_the_pool(client: TestClient) -> None:
    query = client.post("/api/gold/Q001/pool").json()
    query["pool"] = query["pool"] + ["L9"]
    assert client.put("/api/gold/Q001", json=query).status_code == 409


def test_put_rejects_a_body_for_another_query(client: TestClient) -> None:
    query = client.get("/api/gold/Q001").json()
    query["id"] = "Q002"
    assert client.put("/api/gold/Q001", json=query).status_code == 422


def test_put_rejects_a_judgement_outside_the_pool(client: TestClient) -> None:
    query = client.get("/api/gold/Q001").json()
    query["judgements"] = {"L1": 1}
    assert client.put("/api/gold/Q001", json=query).status_code == 422


def test_delete_removes_the_file(client: TestClient, tmp_path: Path) -> None:
    assert client.delete("/api/gold/Q001").status_code == 204
    assert not (tmp_path / "Q001.json").exists()
    assert client.delete("/api/gold/Q001").status_code == 404


def test_listings_are_served_as_text_without_annotations(client: TestClient) -> None:
    listings = client.get("/api/listings").json()
    assert [item["id"] for item in listings] == ["L1", "L2", "L3"]
    assert set(listings[0]) == {"id", "name", "location", "summary", "description", "practical"}


def test_label_page_is_served(client: TestClient) -> None:
    page = client.get("/label.html")
    assert page.status_code == 200
    assert "Every listing here is synthetic" in page.text


def test_build_label_app_pools_from_the_live_index(db: psycopg.Connection, tmp_path: Path) -> None:
    cli.run_index(db, FakeModel(), load_listings())
    gold.save_query(tmp_path, GoldQuery(id="Q001", text="a silent weekend alone"))
    client = TestClient(
        label.build_label_app(FakeModel(), os.environ["TEST_DATABASE_URL"], tmp_path)
    )
    pooled = client.post("/api/gold/Q001/pool").json()
    assert pooled["pool_provenance"] == {
        "embedding_model": embed.MODEL_NAME,
        "embedding_depth": 20,
    }
    assert len(pooled["pool"]) >= 20
