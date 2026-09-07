"""
Threshold: a matching system for wellbeing experiences, with clinical
safety constraints.

`threshold.schema` holds every shared Pydantic model: the intent
dimensions, Listing, QueryIntent, and TriageClass. `threshold.corpus`
loads the synthetic listing corpus from disk. Later milestones add
retrieval, intent extraction, triage, and signal annotation as
subpackages alongside these.
"""

__version__ = "0.1.0"
