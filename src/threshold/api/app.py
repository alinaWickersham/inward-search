"""
HTTP API and static frontend for strategy A.

    uvicorn --factory threshold.api.app:production_app

`create_app` takes the search function as an argument rather than building
it, so tests can run the real routes over a fake model without a download.
"""

from collections.abc import Callable
from pathlib import Path
from typing import Literal

from fastapi import FastAPI, HTTPException
from fastapi.staticfiles import StaticFiles
from fastembed import TextEmbedding
from pydantic import BaseModel, Field

from threshold.corpus import load_listings
from threshold.retrieval import embed, store
from threshold.retrieval.store import Hit
from threshold.schema import Listing, ListingDimensions

# <repo>/frontend/public — the package lives in src/threshold/api/.
FRONTEND_DIR = Path(__file__).resolve().parents[3] / "frontend" / "public"

MAX_QUERY_LENGTH = 1000
MAX_K = 50

SearchFn = Callable[[str, int], list[Hit]]


class SearchRequest(BaseModel):
    """
    Sent as a POST body rather than a query string so that what a person
    writes never appears in server access logs.
    """

    query: str = Field(max_length=MAX_QUERY_LENGTH)
    k: int = Field(default=10, ge=1, le=MAX_K)


class ListingCard(BaseModel):
    """What the results page shows for a listing."""

    id: str
    name: str
    location: str
    summary: str
    dimensions: ListingDimensions
    synthetic: bool


class SearchResult(BaseModel):
    rank: int
    score: float
    listing: ListingCard


class SearchResponse(BaseModel):
    query: str
    strategy: Literal["embedding"]
    model: str
    results: list[SearchResult]


def create_app(search: SearchFn, listings: list[Listing], model_name: str) -> FastAPI:
    by_id = {item.id: item for item in listings}
    app = FastAPI(title="Threshold")

    @app.post("/api/search")
    def search_route(request: SearchRequest) -> SearchResponse:
        query = request.query.strip()
        if not query:
            raise HTTPException(status_code=422, detail="query is empty")
        results = [
            SearchResult(
                rank=rank,
                score=hit.score,
                listing=ListingCard.model_validate(by_id[hit.listing_id].model_dump()),
            )
            for rank, hit in enumerate(search(query, request.k), start=1)
        ]
        return SearchResponse(query=query, strategy="embedding", model=model_name, results=results)

    app.mount("/", StaticFiles(directory=FRONTEND_DIR, html=True), name="frontend")
    return app


def build_app(model: TextEmbedding, database_url: str) -> FastAPI:
    """
    The app over a live index. Refuses to start if the index was built by a
    different model or from a different set of listings than the corpus on
    disk, because either would return results that do not match the text.
    """
    listings = load_listings()
    conn = store.connect(database_url)
    if store.indexed_model(conn) != embed.MODEL_NAME:
        raise RuntimeError("index was built with a different model; run the index command")
    if store.indexed_listing_ids(conn) != {item.id for item in listings}:
        raise RuntimeError("index does not match the corpus; run the index command")

    def search(query: str, k: int) -> list[Hit]:
        return store.search(conn, embed.embed_query(model, query), k)

    return create_app(search, listings, embed.MODEL_NAME)


def production_app() -> FastAPI:
    return build_app(embed.load_model(), store.database_url())
