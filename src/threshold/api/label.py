"""
Local labelling tool for the gold query set. Writes to eval/gold/.

    uvicorn --factory threshold.api.label:production_label_app
    # open http://127.0.0.1:8000/label.html

This is a separate app from the search API so that the search app has no
write routes at all. It is meant to run on the labeller's own machine.
"""

from collections.abc import Callable
from pathlib import Path

from fastapi import FastAPI, HTTPException, Response
from fastapi.staticfiles import StaticFiles
from fastembed import TextEmbedding
from pydantic import BaseModel, Field

from threshold.api.app import FRONTEND_DIR, MAX_QUERY_LENGTH, open_checked_index
from threshold.corpus import load_listings
from threshold.eval import gold, pool
from threshold.eval.gold import GoldQuery
from threshold.retrieval import embed, store
from threshold.schema import Listing

EmbeddingTopFn = Callable[[str], list[str]]


class QuerySummary(BaseModel):
    id: str
    text: str
    triage_set: bool
    pool_size: int
    judged: int
    complete: bool


class NewQuery(BaseModel):
    text: str = Field(min_length=1, max_length=MAX_QUERY_LENGTH)


class ListingText(BaseModel):
    """
    What the labeller reads. The annotated dimensions are left out on
    purpose: relevance is judged from the text, as a reader would, not from
    labels that would favour the structured strategies.
    """

    id: str
    name: str
    location: str
    summary: str
    description: str
    practical: str


def _summary(query: GoldQuery) -> QuerySummary:
    return QuerySummary(
        id=query.id,
        text=query.text,
        triage_set=query.triage is not None,
        pool_size=len(query.pool),
        judged=len(query.judgements),
        complete=query.complete,
    )


def _load(gold_dir: Path, query_id: str) -> GoldQuery:
    try:
        return gold.load_query(gold_dir, query_id)
    except ValueError as error:
        raise HTTPException(status_code=422, detail=str(error)) from error
    except FileNotFoundError as error:
        raise HTTPException(status_code=404, detail=f"no query {query_id}") from error


def create_label_app(
    embedding_top: EmbeddingTopFn,
    embedding_model: str,
    listings: list[Listing],
    partners: dict[str, str],
    gold_dir: Path,
) -> FastAPI:
    app = FastAPI(title="Threshold labelling")
    listing_texts = [ListingText.model_validate(item.model_dump()) for item in listings]

    @app.get("/api/gold")
    def list_queries() -> list[QuerySummary]:
        return [_summary(query) for query in gold.load_gold(gold_dir)]

    @app.post("/api/gold", status_code=201)
    def add_query(new: NewQuery) -> GoldQuery:
        text = new.text.strip()
        if not text:
            raise HTTPException(status_code=422, detail="query is empty")
        query = GoldQuery(id=gold.next_query_id(gold_dir), text=text)
        gold.save_query(gold_dir, query)
        return query

    @app.get("/api/gold/{query_id}")
    def get_query(query_id: str) -> GoldQuery:
        return _load(gold_dir, query_id)

    @app.put("/api/gold/{query_id}")
    def update_query(query_id: str, query: GoldQuery) -> GoldQuery:
        """Saves text, intent, triage, and judgements. The pool changes only through /pool."""
        stored = _load(gold_dir, query_id)
        if query.id != query_id:
            raise HTTPException(status_code=422, detail="id in the body does not match the URL")
        if query.pool != stored.pool or query.pool_provenance != stored.pool_provenance:
            raise HTTPException(status_code=409, detail="the pool changed; reload the query")
        gold.save_query(gold_dir, query)
        return query

    @app.post("/api/gold/{query_id}/pool")
    def build_pool(query_id: str) -> GoldQuery:
        query = _load(gold_dir, query_id)
        top = embedding_top(query.text)
        query = pool.extend_pool(query, top, listings, partners, embedding_model)
        gold.save_query(gold_dir, query)
        return query

    @app.delete("/api/gold/{query_id}", status_code=204)
    def delete_query(query_id: str) -> Response:
        _load(gold_dir, query_id)
        gold.path_for(gold_dir, query_id).unlink()
        return Response(status_code=204)

    @app.get("/api/listings")
    def get_listings() -> list[ListingText]:
        return listing_texts

    app.mount("/", StaticFiles(directory=FRONTEND_DIR, html=True), name="frontend")
    return app


def build_label_app(model: TextEmbedding, database_url: str, gold_dir: Path) -> FastAPI:
    listings = load_listings()
    conn = open_checked_index(database_url, listings)

    def embedding_top(text: str) -> list[str]:
        hits = store.search(conn, embed.embed_query(model, text), pool.EMBEDDING_DEPTH)
        return [hit.listing_id for hit in hits]

    partners = pool.near_duplicate_partners()
    return create_label_app(embedding_top, embed.MODEL_NAME, listings, partners, gold_dir)


def production_label_app() -> FastAPI:
    return build_label_app(embed.load_model(), store.database_url(), gold.GOLD_DIR)
