"""
App factory for the Playwright tests in frontend/e2e/.

Indexes the real corpus into TEST_DATABASE_URL with the fake model, then
serves the real app over it. Everything but the embedding model is the
production path.

    uvicorn --factory tests.e2e_server:app
"""

import os

from fastapi import FastAPI

from tests.conftest import FakeModel
from threshold.api.app import build_app
from threshold.corpus import load_listings
from threshold.retrieval import cli, store


def app() -> FastAPI:
    url = os.environ["TEST_DATABASE_URL"]
    with store.connect(url) as conn:
        cli.run_index(conn, FakeModel(), load_listings())
    return build_app(FakeModel(), url)
