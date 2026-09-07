"""Load the synthetic corpus from disk and validate it against the schema."""

from threshold.corpus.loader import CORPUS_DIR, load_listings, load_seeds

__all__ = ["CORPUS_DIR", "load_listings", "load_seeds"]
