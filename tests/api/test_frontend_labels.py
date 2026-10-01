"""
The frontend keeps its own copy of the schema's values for display and for
the labelling page's choices. These tests fail when the schema changes in
Python without the matching change in frontend/src/labels.ts.
"""

import re
from enum import Enum
from pathlib import Path

from threshold.schema import ListingDimensions, TriageClass

LABELS_TS = (Path(__file__).resolve().parents[2] / "frontend" / "src" / "labels.ts").read_text()


def block(name: str) -> str:
    """The body of `export const NAME ... = { ... };` in labels.ts."""
    match = re.search(rf"export const {name}\b.*?= \{{(.*?)\n\}};", LABELS_TS, flags=re.DOTALL)
    assert match, f"{name} not found in labels.ts"
    return match.group(1)


def schema_values(field: str) -> list[str]:
    enum: type[Enum] = ListingDimensions.model_fields[field].annotation  # type: ignore[assignment]
    return [member.value for member in enum]


def test_every_schema_value_has_a_display_label() -> None:
    labelled = set(re.findall(r"^\s+(\w+): \"", block("VALUE_LABELS"), flags=re.MULTILINE))
    for field in ListingDimensions.model_fields:
        missing = set(schema_values(field)) - labelled
        assert not missing, f"no label in VALUE_LABELS for {sorted(missing)}"


def test_dimension_values_match_the_schema_in_order() -> None:
    lists = dict(re.findall(r"(\w+): \[(.*?)\]", block("DIMENSION_VALUES"), flags=re.DOTALL))
    assert list(lists) == list(ListingDimensions.model_fields)
    for field, body in lists.items():
        assert re.findall(r'"(\w+)"', body) == schema_values(field), field


def test_triage_labels_cover_exactly_the_triage_classes() -> None:
    keys = re.findall(r"^\s+(\w+): \"", block("TRIAGE_LABELS"), flags=re.MULTILINE)
    assert keys == [member.value for member in TriageClass]
