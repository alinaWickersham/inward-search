"""
Retrieval strategies (Module 1).

Three strategies share one interface so the evaluation can compare them on
the same labeled query set:

    A. EmbeddingOnly   — embed the raw query, cosine similarity over listings
    B. StructuredOnly  — extract intent, filter and score on dimensions alone
    C. Hybrid          — structured intent constrains and weights dense retrieval

Weekend 2 ships A. Weekend 3 ships B. Weekend 4 ships C and the comparison.
"""

from threshold.retrieval.base import RetrievalStrategy, ScoredListing

__all__ = ["RetrievalStrategy", "ScoredListing"]
