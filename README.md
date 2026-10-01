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
| **1. Intent matching** | Nine-dimension intent schema; three retrieval strategies (embedding-only, structured-only, hybrid) compared on one labeled query set | Schema and corpus done; strategy A (embedding only) built, not yet evaluated |
| **2. Trust & contraindication signals** | Descriptive signals about what a listing says, and does not say, about screening, teachers, pricing, and risky practices. Never a verdict. | Not started |
| **3. Triage & routing** | Classifies the kind of need a query expresses and escalates what is *offered*, never what is *withheld* | Enum defined |

## Repository layout

```
src/threshold/            the package, installed with `pip install -e .`
  schema.py               dimensions, Listing, QueryIntent, TriageClass (single source of truth)
  corpus/                 loads the synthetic corpus, refuses anything not marked synthetic
  retrieval/              strategy A: fastembed embeddings, pgvector store, CLI
  eval/                   recall@k, MRR, nDCG; the gold set model and pooling
  api/                    FastAPI: POST /api/search and the frontend; label.py is the labelling app

eval/gold/                the gold queries and their labels, one JSON per query

corpus/                   the synthetic listings
  seeds.json              3 hand-written listings that set the register
  plan.json               120 listing specs, deterministic from scripts/coverage.py
  listings/               one JSON per listing, written from the plan

frontend/                 one search page in TypeScript, compiled by tsc
  src/                    API client, rendering, form wiring
  public/                 index.html, style.css, and tsc output in dist/
  tests/                  vitest unit tests (jsdom)
  e2e/                    Playwright tests against the running app

scripts/
  coverage.py             builds corpus/plan.json
  check_corpus.py         validates listings against the plan and schema

docs/
  SPEC.md                 the full project specification
  decisions/              short records of the choices a reader might question
  phases/                 one working doc per phase

tests/                    pytest, mirroring src/
docker-compose.yml        PostgreSQL with pgvector
```

Intent extraction, triage, and signals are added as subpackages of
`threshold` in the phases that build them.

## Getting started

```bash
python -m venv .venv && source .venv/bin/activate
pip install -e ".[pipeline,api,dev]"

python -m pytest -q                              # see Tests below for the database tests
python scripts/coverage.py > corpus/plan.json    # rebuild the plan (deterministic)
python scripts/check_corpus.py                   # validate listings against plan and schema
```

The listings were written from the plan by a Claude model working in a
Claude Code session, one file per plan entry, and then read and edited by
hand. Each listing records the model that wrote it. There is no generation
script to run; the corpus is a committed artefact.

### Strategy A: embedding search

```bash
docker compose up -d                              # Postgres + pgvector on :5432

python -m threshold.retrieval index               # embed the corpus (downloads the model once)
python -m threshold.retrieval search "somewhere quiet, I am worn out" -k 5

(cd frontend && npm install && npm run build)     # compile the page
uvicorn --factory threshold.api.app:production_app
# open http://127.0.0.1:8000
```

`DATABASE_URL` points at a different database; the default matches
`docker-compose.yml`. The model is `BAAI/bge-small-en-v1.5` through
fastembed; see [decision 0006](docs/decisions/0006-embedding-model-and-store.md).

### Tests

```bash
export TEST_DATABASE_URL=postgresql://postgres:postgres@localhost:5432/threshold_test
python -m pytest -q                               # without the variable, database tests skip

cd frontend
npm test                                          # vitest unit tests
npm run typecheck                                 # tsc over src and tests
npm run e2e                                       # Playwright, starts the app itself
```

The database and Playwright tests use a real Postgres and the real corpus,
but a hashed bag-of-words stand-in for the embedding model. They check that
indexing, ranking, the API, and the page behave correctly. They say nothing
about how well bge ranks listings; that is what the phase 4 evaluation is
for. pytest and Playwright share `threshold_test`, so run them one at a time.

CI (`.github/workflows/ci.yml`) runs all of the above on every pull request
and on pushes to `main`, each job with its own pgvector database.

### Labelling the gold set

The gold queries live in `eval/gold/`, one JSON file per query. They are
labelled in a local page served by a separate app that can write to that
folder:

```bash
python -m threshold.retrieval index                      # the pool uses strategy A
(cd frontend && npm run build)
uvicorn --factory threshold.api.label:production_label_app
# open http://127.0.0.1:8000/label.html
```

For each query: set the intent, set the triage class, build the pool, then
judge each listing with `1` (relevant) or `0` (not relevant); `j` and `k`
move. Every change is saved immediately. Commit `eval/gold/` when done.
How the pool is built, and what that biases, is in
[decision 0008](docs/decisions/0008-gold-set-labelling.md).

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
| 2 | Retrieval baseline: embeddings in pgvector, strategy A from a CLI | built; a simple search page was added early |
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
