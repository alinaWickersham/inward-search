"""
App factories for the Playwright tests in frontend/e2e/.

Each indexes the real corpus into TEST_DATABASE_URL with the fake model,
then serves the real app over it. Everything but the embedding model is the
production path. The labelling app writes to a fresh temporary directory
seeded with one query, never to eval/gold/.

    uvicorn --factory tests.e2e_server:app
    uvicorn --factory tests.e2e_server:label_app
"""

import os
import tempfile
from pathlib import Path

from fastapi import FastAPI

from tests.conftest import FakeModel
from threshold.api.app import build_app
from threshold.api.label import build_label_app
from threshold.corpus import load_listings
from threshold.eval import gold
from threshold.eval.gold import GoldQuery
from threshold.retrieval import cli, store


def _index() -> str:
    url = os.environ["TEST_DATABASE_URL"]
    with store.connect(url) as conn:
        cli.run_index(conn, FakeModel(), load_listings())
    return url


def app() -> FastAPI:
    return build_app(FakeModel(), _index())


def label_app() -> FastAPI:
    gold_dir = Path(tempfile.mkdtemp(prefix="gold-e2e-"))
    gold.save_query(gold_dir, GoldQuery(id="Q001", text="i want to be somewhere silent, alone"))
    return build_label_app(FakeModel(), _index(), gold_dir)
