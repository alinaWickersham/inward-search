# 0006. Strategy A uses fastembed with bge-small, stored in pgvector, searched exactly

Date: 2026-10-01
Status: accepted

## Context

Strategy A needs an embedding model and somewhere to keep 120 listing
vectors. The model must be reproducible from a clean checkout with no API
key, and the ranking it produces must be the same on every run, because the
three-strategy comparison is only meaningful if A is a stable baseline.

## Decision

- Model: `BAAI/bge-small-en-v1.5` (384 dimensions), run locally on CPU
  through fastembed's ONNX runtime. Listings are embedded with the passage
  method and queries with the query method, as bge expects.
- What is embedded: name, summary, description, and practical text. Not the
  annotated dimensions; A is the text-only baseline.
- Store: PostgreSQL with pgvector, as the spec planned. Only vectors and the
  model name are stored; listings stay in `corpus/listings/`.
- Search: exact cosine, no HNSW or IVFFlat index, ties broken by listing id.

## Alternatives considered

**sentence-transformers.** Better known, but it pulls in torch, about 2GB,
to run one small model.

**An API embedding model.** Possibly stronger, but it needs a key and costs
money per run, and the provider can change the model behind the name.

**numpy in memory instead of pgvector.** At 120 rows it would rank the same
listings identically with no service to run. pgvector was kept because
strategies B and C need structured filters and vector search in one query,
and setting up the store once now is cheaper than migrating to it in phase 4.

**An approximate index.** Saves nothing at this size and makes rankings
depend on index parameters.

## Consequences

Running A needs Docker (or a local Postgres with pgvector) and a one-time
model download into the fastembed cache. Tests do not need the model: they
use a deterministic hashed bag-of-words stand-in, so test results say nothing
about bge's ranking quality. Changing the model means rebuilding the index;
the API refuses to start against an index built by another model.
