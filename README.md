# Threshold

**A matching system for wellbeing experiences, with clinical safety constraints.**

> **Everything in this repository is synthetic.** The retreat listings are
> fictional and generated for testing. Nothing here is medical advice, and the
> system never diagnoses, assesses, or withholds results based on what a person
> writes. See [Legal posture](docs/SPEC.md#legal-posture).

People describe what they need from a retreat as a felt state, not a filter
set: *"I have been running on empty and I want to be somewhere quiet with
people who will not ask me about work."* Threshold turns that sentence into
structured intent, retrieves against it, and explains each match.

The harder problem is that the same sentence is sometimes spiritual seeking and
sometimes untreated depression. So the system also carries a **triage layer**
that surfaces support resources without ever gating results, and a
**contraindication layer** grounded in the adverse-effects literature. The
evaluation reports false negatives on the high-need classes separately, because
that is the number that actually matters.

Full specification: [`docs/SPEC.md`](docs/SPEC.md).

## Three modules

| Module | What it does | Status |
|---|---|---|
| **1. Intent matching** | Nine-dimension intent schema; three retrieval strategies (embedding-only, structured-only, hybrid) compared on one labeled query set | Schema done, corpus plan done |
| **2. Trust & contraindication signals** | Descriptive signals about what a listing says, and does not say, about screening, teachers, pricing, and risky practices. Never a verdict. | Not started |
| **3. Triage & routing** | Classifies the kind of need a query expresses and escalates what is *offered*, never what is *withheld* | Enum defined |

## Repository layout

```
src/threshold/            the package, installed with `pip install -e .`
  schema.py               dimensions, Listing, QueryIntent, TriageClass (single source of truth)
  corpus/                 loads the synthetic corpus, refuses anything not marked synthetic

corpus/                   the synthetic listings
  seeds.json              3 hand-written listings that set the register
  plan.json               120 listing specs, deterministic from scripts/coverage.py
  listings/               one JSON per listing, written from the plan

scripts/
  coverage.py             builds corpus/plan.json
  check_corpus.py         validates listings against the plan and schema

docs/
  SPEC.md                 the full project specification
  decisions/              short records of the choices a reader might question
  phases/                 one working doc per phase

tests/                    pytest
```

Retrieval, intent extraction, triage, signals, evaluation, and the API are
added as subpackages of `threshold` in the phases that build them.

## Getting started

```bash
python -m venv .venv && source .venv/bin/activate
pip install -e ".[dev]"

python -m pytest -q                              # schema + plan reproducibility
python scripts/coverage.py > corpus/plan.json    # rebuild the plan (deterministic)
python scripts/check_corpus.py                   # validate listings against plan and schema
```

The listings were written from the plan by a Claude model working in a
Claude Code session, one file per plan entry, and then read and edited by
hand. Each listing records the model that wrote it. There is no generation
script to run; the corpus is a committed artefact.

## The intent dimensions

Every listing is annotated on nine axes, and every query is parsed into a
*partial* specification over the same axes. Absence means "no preference",
which is different from a middle value.

| Dimension | Values |
|---|---|
| Social | solitude · small group · community |
| Structure | fixed · semi-structured · self-directed |
| Speech | full silence · partial silence · dialogue |
| Guidance | teacher-led · light guidance · self-guided |
| Physical demand | restful · moderate · demanding |
| Tradition | secular · Buddhist-derived · yogic · contemplative Christian · nature-based · eclectic |
| Experience level | newcomer-friendly · some experience · assumes practice |
| Duration | hours · weekend · week · extended |
| Cost band | free/donation · low · mid · high |

Defined in [`src/threshold/schema.py`](src/threshold/schema.py). Changing a
dimension later means re-annotating the corpus and the gold set, so phase 1
is mostly about deciding whether these nine are right.

## Design commitments

These are constraints, not aspirations. Code that violates them is a bug.
The reasoning behind each is in [`docs/decisions/`](docs/decisions/).

- **Surface, never gate.** Triage changes what resources are offered and how
  prominently. It never removes, filters, or reorders results.
- **No assessment language.** The system never names or implies a condition,
  never scores the person, never says "you appear to be…".
- **Nothing about the person is stored.** Triage classifications are computed
  per request and discarded.
- **Signals are descriptive.** "This listing does not name its teachers." Not
  "this is a cult." The reader decides.
- **The corpus is synthetic.** Trust signals are never applied to a real,
  named organisation.

## Evaluation

| Area | Measures |
|---|---|
| Retrieval | recall@5, recall@10, MRR, nDCG across strategies A/B/C |
| Intent extraction | per-dimension accuracy against gold intents |
| Signals | precision and recall per signal category |
| **Triage** | precision and recall per class, **false negatives on the two highest-need classes reported separately** |
| Cost and latency | per query, per strategy |

The write-up will include a section on what this evaluation cannot tell you:
synthetic corpus, single annotator, no real users, no clinical validation.

## Phases

| Phase | Ships | |
|---|---|---|
| 1 | Corpus: coverage plan, 120 listings, annotations | in progress |
| 2 | Retrieval baseline: embeddings in pgvector, strategy A from a CLI | |
| 3 | Intent extraction, strategy B, 50-query gold set | |
| 4 | Hybrid strategy C, full metrics, comparison table — **minimum shippable** | |
| 5 | Triage classification, routing, response assembly | |
| 6 | Trust and contraindication taxonomy, extraction, small trained classifier | |
| 7 | Langfuse tracing, cost/latency, FastAPI | |
| 8 | Docker, k3s on EC2, minimal frontend | |
| 9 | Write-up, charts, legal-posture note | |

Per-phase working notes live in [`docs/phases/`](docs/phases/).

## Stack

LangGraph · Pydantic · PostgreSQL + pgvector · Langfuse · FastAPI ·
scikit-learn · Docker · k3s on EC2. Two or three LLMs, at least one
open-weight, for comparison and cost realism.

## License

MIT.
