"""
Threshold — a matching system for wellbeing experiences, with clinical
safety constraints.

Package layout follows the pipeline:

    query
      -> triage        (threshold.triage)      classify the kind of need
      -> intent        (threshold.intent)      felt state -> structured dimensions
      -> retrieval     (threshold.retrieval)   strategies A / B / C
      -> signals       (threshold.signals)     trust + contraindication annotation
      -> evaluation    (threshold.evaluation)  metrics over the gold query set
      -> api           (threshold.api)         FastAPI wrapper

`threshold.schema` holds every shared Pydantic model. `threshold.corpus`
loads the synthetic listing corpus from disk.
"""

__version__ = "0.1.0"
