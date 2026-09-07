"""The interface every retrieval strategy implements."""

from typing import Protocol

from pydantic import BaseModel

from threshold.schema import Listing, QueryIntent


class ScoredListing(BaseModel):
    listing: Listing
    score: float
    explanation: str | None = None  # why it matched — shown to the user


class RetrievalStrategy(Protocol):
    """A pluggable strategy. `intent` is None for strategy A, which never
    extracts one; B and C receive the parsed intent alongside the raw query."""

    name: str

    def retrieve(
        self,
        query: str,
        intent: QueryIntent | None,
        k: int = 10,
    ) -> list[ScoredListing]: ...
