"""
Listing embeddings in PostgreSQL with pgvector.

Only vectors live in the database. The listings themselves stay in
corpus/listings/, which is the committed source of truth; a hit carries
the listing id and the caller joins it back to the corpus.

Search is exact (sequential scan, no HNSW or IVFFlat index). At 120 rows
an approximate index saves nothing and would make rankings depend on index
build parameters, which the strategy comparison must not.
"""

import os

import numpy as np
import psycopg
from pgvector.psycopg import register_vector
from pydantic import BaseModel

DEFAULT_DATABASE_URL = "postgresql://postgres:postgres@localhost:5432/threshold"


class Hit(BaseModel):
    listing_id: str
    score: float  # cosine similarity, 1.0 is identical direction


def database_url() -> str:
    return os.environ.get("DATABASE_URL", DEFAULT_DATABASE_URL)


def connect(url: str) -> psycopg.Connection:
    """Open a connection with the vector type registered."""
    conn = psycopg.connect(url, autocommit=True)
    conn.execute("CREATE EXTENSION IF NOT EXISTS vector")
    register_vector(conn)
    return conn


def rebuild_index(
    conn: psycopg.Connection, model_name: str, listing_ids: list[str], vectors: np.ndarray
) -> None:
    """
    Replace every stored embedding with these.

    The table is dropped and recreated rather than upserted so that the
    vector width always matches the model, and no row from an earlier
    model or corpus survives a rebuild.
    """
    if len(listing_ids) != len(vectors):
        raise ValueError(f"{len(listing_ids)} ids but {len(vectors)} vectors")
    with conn.transaction():
        conn.execute("DROP TABLE IF EXISTS listing_embedding")
        conn.execute(
            f"CREATE TABLE listing_embedding ("
            f" listing_id text PRIMARY KEY,"
            f" model text NOT NULL,"
            f" embedding vector({vectors.shape[1]}) NOT NULL)"
        )
        with conn.cursor() as cur:
            cur.executemany(
                "INSERT INTO listing_embedding (listing_id, model, embedding) VALUES (%s, %s, %s)",
                [(lid, model_name, vec) for lid, vec in zip(listing_ids, vectors)],
            )


def indexed_model(conn: psycopg.Connection) -> str:
    """The model the stored embeddings came from. Raises if there is no single answer."""
    rows = conn.execute("SELECT DISTINCT model FROM listing_embedding").fetchall()
    if len(rows) != 1:
        raise RuntimeError(f"expected embeddings from one model, found {len(rows)}")
    return rows[0][0]


def indexed_listing_ids(conn: psycopg.Connection) -> set[str]:
    return {row[0] for row in conn.execute("SELECT listing_id FROM listing_embedding")}


def search(conn: psycopg.Connection, query_vector: np.ndarray, k: int) -> list[Hit]:
    """
    The k listings nearest the query by cosine similarity, best first.

    Equal scores are broken by listing id so that a ranking is the same on
    every run.
    """
    if k < 1:
        raise ValueError("k must be at least 1")
    rows = conn.execute(
        "SELECT listing_id, 1 - (embedding <=> %s) AS score FROM listing_embedding"
        " ORDER BY embedding <=> %s, listing_id LIMIT %s",
        (query_vector, query_vector, k),
    ).fetchall()
    return [Hit(listing_id=lid, score=score) for lid, score in rows]
