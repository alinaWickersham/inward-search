"""
Shared fixtures.

Tests that need pgvector read TEST_DATABASE_URL and are skipped when it is
unset. Each test gets the database with its embedding table dropped, so
tests do not see each other's rows.
"""

import os
import re
import zlib
from collections.abc import Iterable, Iterator

import numpy as np
import psycopg
import pytest

from threshold.retrieval import store
from threshold.schema import Listing

FAKE_DIMENSION = 32


def fake_vector(text: str) -> np.ndarray:
    """Hashed bag of words, unit length. Deterministic across runs and machines."""
    vector = np.zeros(FAKE_DIMENSION, dtype=np.float32)
    for token in re.findall(r"[a-z]+", text.lower()):
        vector[zlib.crc32(token.encode()) % FAKE_DIMENSION] += 1.0
    return vector / np.linalg.norm(vector)


class FakeModel:
    """
    Stands in for fastembed's TextEmbedding, which cannot be downloaded in
    every test environment. Records which side each call used so tests can
    check that queries and passages are embedded differently.
    """

    def __init__(self) -> None:
        self.calls: list[str] = []

    def passage_embed(self, texts: Iterable[str]) -> Iterator[np.ndarray]:
        self.calls.append("passage")
        return (fake_vector(text) for text in texts)

    def query_embed(self, texts: Iterable[str]) -> Iterator[np.ndarray]:
        self.calls.append("query")
        return (fake_vector(text) for text in texts)


def make_listing(listing_id: str, name: str, summary: str = "", **dimensions: str) -> Listing:
    """A minimal valid listing. Dimension values default to the first of each enum."""
    defaults = {
        "social": "solitude",
        "structure": "fixed",
        "speech": "full_silence",
        "guidance": "teacher_led",
        "physical_demand": "restful",
        "tradition": "secular",
        "experience_level": "newcomer_friendly",
        "duration": "hours",
        "cost_band": "free_or_donation",
    }
    return Listing(
        id=listing_id,
        name=name,
        location="Invented Valley",
        summary=summary,
        description=f"{name} description",
        practical=f"{name} practical",
        dimensions={**defaults, **dimensions},
    )


@pytest.fixture
def fake_model() -> FakeModel:
    return FakeModel()


@pytest.fixture
def db() -> Iterator[psycopg.Connection]:
    url = os.environ.get("TEST_DATABASE_URL")
    if not url:
        pytest.skip("TEST_DATABASE_URL is not set")
    with store.connect(url) as conn:
        conn.execute("DROP TABLE IF EXISTS listing_embedding")
        yield conn
