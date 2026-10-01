"""
Which listings get judged for a query.

Judging all 120 listings for every query is too slow, so each query is
judged on a pool: the embedding strategy's top results, every listing that
matches the gold intent on all the dimensions it constrains, and the
near-duplicate partner of anything already in the pool. Unjudged listings
count as not relevant. Decision 0008 covers the bias this introduces.

The pool is shown in a seeded shuffle rather than ranked order, so the
labeller cannot see which listings strategy A preferred.
"""

import json
import random
from pathlib import Path

from threshold.corpus import CORPUS_DIR
from threshold.eval.gold import GoldIntent, GoldQuery, PoolProvenance
from threshold.schema import Listing

EMBEDDING_DEPTH = 20


def near_duplicate_partners(corpus_dir: Path = CORPUS_DIR) -> dict[str, str]:
    """Listing id -> its pair partner, read from the `pair` field the corpus files carry."""
    members: dict[str, list[str]] = {}
    for path in sorted((corpus_dir / "listings").glob("*.json")):
        data = json.loads(path.read_text())
        if data.get("pair"):
            members.setdefault(data["pair"], []).append(data["id"])
    partners: dict[str, str] = {}
    for pair, ids in members.items():
        if len(ids) != 2:
            raise ValueError(f"{pair} has {len(ids)} members, expected 2")
        partners[ids[0]], partners[ids[1]] = ids[1], ids[0]
    return partners


def matches_intent(listing: Listing, intent: GoldIntent) -> bool:
    """
    True if the listing satisfies every dimension the intent constrains.
    An intent that constrains nothing matches nothing here, because adding
    the whole corpus to the pool would defeat pooling.
    """
    constraints = {dim: values for dim, values in intent if values}
    if not constraints:
        return False
    dimensions = listing.dimensions
    return all(getattr(dimensions, dim) in values for dim, values in constraints.items())


def extend_pool(
    query: GoldQuery,
    embedding_top: list[str],
    listings: list[Listing],
    partners: dict[str, str],
    embedding_model: str,
) -> GoldQuery:
    """
    The query with any new candidates appended to its pool.

    Existing pool members and judgements are never removed, so changing
    the intent after judging only adds listings to judge.
    """
    candidates = set(embedding_top) | {
        item.id for item in listings if matches_intent(item, query.intent)
    }
    candidates |= {partners[lid] for lid in candidates if lid in partners}
    new = sorted(candidates - set(query.pool))
    random.Random(query.id).shuffle(new)
    return query.model_copy(
        update={
            "pool": query.pool + new,
            "pool_provenance": PoolProvenance(
                embedding_model=embedding_model, embedding_depth=len(embedding_top)
            ),
        }
    )
