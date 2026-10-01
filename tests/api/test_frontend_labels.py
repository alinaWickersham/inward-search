"""
The frontend keeps its own display labels for dimension values. This
catches a schema value added in Python without a label in TypeScript,
which would otherwise show up only as raw snake_case on the page.
"""

import re
from enum import Enum
from pathlib import Path

from threshold.schema import ListingDimensions

LABELS_TS = Path(__file__).resolve().parents[2] / "frontend" / "src" / "labels.ts"


def test_every_schema_value_has_a_frontend_label() -> None:
    labelled = set(re.findall(r"^\s+(\w+): \"", LABELS_TS.read_text(), flags=re.MULTILINE))
    for field in ListingDimensions.model_fields.values():
        enum: type[Enum] = field.annotation  # type: ignore[assignment]
        missing = {member.value for member in enum} - labelled
        assert not missing, f"no label in labels.ts for {sorted(missing)}"
