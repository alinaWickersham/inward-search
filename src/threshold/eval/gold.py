"""
The gold query set: hand-written queries with hand-labelled intent, triage
class, and relevance judgements. One JSON file per query in eval/gold/.

These are evaluation labels on queries the owner wrote, not records about
a person, which is why the triage class may be stored here; see decision
0008.
"""

import os
import re
from pathlib import Path
from typing import Literal

from pydantic import BaseModel, Field, model_validator

from threshold.schema import (
    CostBand,
    Duration,
    ExperienceLevel,
    Guidance,
    PhysicalDemand,
    Social,
    Speech,
    Structure,
    Tradition,
    TriageClass,
)

# <repo>/eval/gold — the package lives in src/threshold/eval/.
GOLD_DIR = Path(__file__).resolve().parents[3] / "eval" / "gold"

QUERY_ID = re.compile(r"^Q\d{3}$")


class GoldIntent(BaseModel):
    """
    The dimensions a query constrains. A list rather than a single value
    because people write "a weekend or a week"; an empty list means no
    preference. Extraction counts as correct if it picks any listed value.
    """

    social: list[Social] = []
    structure: list[Structure] = []
    speech: list[Speech] = []
    guidance: list[Guidance] = []
    physical_demand: list[PhysicalDemand] = []
    tradition: list[Tradition] = []
    experience_level: list[ExperienceLevel] = []
    duration: list[Duration] = []
    cost_band: list[CostBand] = []


class PoolProvenance(BaseModel):
    """How the pool was built, so the judged set can be reproduced."""

    embedding_model: str
    embedding_depth: int


class GoldQuery(BaseModel):
    id: str = Field(pattern=QUERY_ID.pattern)
    text: str = Field(min_length=1)
    intent: GoldIntent = GoldIntent()
    triage: TriageClass | None = None  # None until labelled
    pool: list[str] = []  # listings to judge, in the order they are shown
    pool_provenance: PoolProvenance | None = None
    judgements: dict[str, Literal[0, 1]] = {}  # listing id -> relevant or not

    @model_validator(mode="after")
    def judgements_are_in_pool(self) -> "GoldQuery":
        stray = set(self.judgements) - set(self.pool)
        if stray:
            raise ValueError(f"judged listings not in the pool: {sorted(stray)}")
        if len(set(self.pool)) != len(self.pool):
            raise ValueError("pool repeats a listing")
        return self

    @property
    def complete(self) -> bool:
        """Labelled enough to evaluate: triage set, pool built, every pool listing judged."""
        return (
            self.triage is not None and bool(self.pool) and len(self.judgements) == len(self.pool)
        )

    @property
    def relevant(self) -> set[str]:
        return {lid for lid, grade in self.judgements.items() if grade == 1}


def path_for(gold_dir: Path, query_id: str) -> Path:
    """The file for a query id. Rejects anything that is not a query id, so no path escapes."""
    if not QUERY_ID.match(query_id):
        raise ValueError(f"not a query id: {query_id!r}")
    return gold_dir / f"{query_id}.json"


def load_query(gold_dir: Path, query_id: str) -> GoldQuery:
    return GoldQuery.model_validate_json(path_for(gold_dir, query_id).read_text())


def load_gold(gold_dir: Path = GOLD_DIR) -> list[GoldQuery]:
    """Every query on disk, sorted by id."""
    return [GoldQuery.model_validate_json(p.read_text()) for p in sorted(gold_dir.glob("Q*.json"))]


def save_query(gold_dir: Path, query: GoldQuery) -> None:
    """Write via a temporary file and rename, so a crash never leaves a half-written label."""
    target = path_for(gold_dir, query.id)
    gold_dir.mkdir(parents=True, exist_ok=True)
    temporary = target.with_suffix(".json.tmp")
    temporary.write_text(query.model_dump_json(indent=2) + "\n")
    os.replace(temporary, target)


def next_query_id(gold_dir: Path) -> str:
    numbers = [int(p.stem[1:]) for p in gold_dir.glob("Q*.json") if QUERY_ID.match(p.stem)]
    return f"Q{max(numbers, default=0) + 1:03d}"
