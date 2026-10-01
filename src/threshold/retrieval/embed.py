"""
Embedding model for strategy A.

The model runs locally through fastembed (ONNX, CPU, no API key). Listings
and queries go through different methods because bge models are trained
with a retrieval instruction on the query side only.
"""

import numpy as np
from fastembed import TextEmbedding

from threshold.schema import Listing

MODEL_NAME = "BAAI/bge-small-en-v1.5"


def load_model() -> TextEmbedding:
    """Load the model, downloading weights to the fastembed cache on first use."""
    return TextEmbedding(MODEL_NAME)


def listing_text(listing: Listing) -> str:
    """
    The text embedded for a listing: everything a reader of the listing sees.

    The annotated dimensions are deliberately left out. Strategy A is the
    text-only baseline, and embedding the labels would leak the structured
    annotation into it.
    """
    return "\n\n".join([listing.name, listing.summary, listing.description, listing.practical])


def embed_listings(model: TextEmbedding, listings: list[Listing]) -> np.ndarray:
    """One row per listing, in the order given."""
    return np.stack(list(model.passage_embed([listing_text(item) for item in listings])))


def embed_query(model: TextEmbedding, query: str) -> np.ndarray:
    return next(iter(model.query_embed([query])))
