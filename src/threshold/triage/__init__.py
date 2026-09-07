"""
Triage and routing (Module 3, weekend 5).

Design principle: SURFACE, NEVER GATE. The classifier decides what the
system *offers* (support resources, and how prominently), never what it
*withholds*. See docs/SPEC.md, "Module 3", for the full constraints:

  - never name or imply a condition
  - never score or rate the person
  - never remove or reorder results based on inferred mental state
  - never store the classification
  - never use assessment language ("you appear to be…")

The `TriageClass` enum lives in `threshold.schema`.
"""
