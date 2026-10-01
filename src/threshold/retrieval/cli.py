"""
Command line for strategy A.

    python -m threshold.retrieval index
    python -m threshold.retrieval search "somewhere quiet for a weekend" -k 5

DATABASE_URL selects the database; the default matches docker-compose.yml.
"""

import argparse

import psycopg
from fastembed import TextEmbedding

from threshold.corpus import load_listings
from threshold.retrieval import embed, store
from threshold.schema import Listing


def run_index(conn: psycopg.Connection, model: TextEmbedding, listings: list[Listing]) -> str:
    vectors = embed.embed_listings(model, listings)
    store.rebuild_index(conn, embed.MODEL_NAME, [item.id for item in listings], vectors)
    return f"indexed {len(listings)} listings with {embed.MODEL_NAME}"


def run_search(
    conn: psycopg.Connection, model: TextEmbedding, listings: list[Listing], query: str, k: int
) -> str:
    """Ranked results as printable lines: rank, score, id, name."""
    by_id = {item.id: item for item in listings}
    hits = store.search(conn, embed.embed_query(model, query), k)
    return "\n".join(
        f"{rank:>2}  {hit.score:.3f}  {hit.listing_id}  {by_id[hit.listing_id].name}"
        for rank, hit in enumerate(hits, start=1)
    )


def parse_args(argv: list[str] | None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(prog="python -m threshold.retrieval")
    commands = parser.add_subparsers(dest="command", required=True)
    commands.add_parser("index", help="embed the corpus and rebuild the pgvector table")
    search = commands.add_parser("search", help="rank listings against a query")
    search.add_argument("query")
    search.add_argument("-k", type=int, default=10)
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> None:
    args = parse_args(argv)
    model = embed.load_model()
    listings = load_listings()
    with store.connect(store.database_url()) as conn:
        if args.command == "index":
            print(run_index(conn, model, listings))
        else:
            print(run_search(conn, model, listings, args.query, args.k))
