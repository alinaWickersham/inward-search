# 0004. Retrieval is evaluated as three strategies on one gold set

Date: 2026-09-07
Status: accepted

## Context

The technical question at the centre of the project is whether decomposing
a felt-state query into structured dimensions beats embedding the raw query.
This is not obvious in either direction, and a single pipeline would not
answer it.

## Decision

Three strategies share one interface and are run against the same
hand-labeled query set of roughly fifty queries:

- A. Embedding only: embed the raw query, cosine similarity over listings.
- B. Structured only: extract intent, filter and score on dimensions.
- C. Hybrid: structured intent constrains and weights dense retrieval.

Reported as recall@5, recall@10, MRR, and nDCG per strategy, plus cost and
latency per query. The corpus contains near-duplicate pairs differing on
exactly one dimension so that a strategy which ignores that dimension is
visibly penalised. Metric code is written by hand and tested against
hand-computed values.

There are three strategies and there will be three. This is a comparison,
not a plugin system.

## Alternatives considered

**Build only the hybrid.** Faster to a working product, but produces no
finding. Without A as a baseline there is no way to say whether the
structured work earned its cost.

**Compare embedding models instead of strategies.** A real question, but a
different one, and one that is already well covered elsewhere.

**Use an LLM as the judge of relevance.** Cheaper than hand labels, but
then the evaluation measures agreement between two models. Hand labels by
one annotator are weaker than a panel and stronger than that.

## Consequences

The project produces an answer to a genuinely open question, with numbers.
The gold set is the bottleneck: fifty queries, one annotator, synthetic
corpus, and the write-up must say what that cannot tell you. The shared
interface is the one abstraction in the retrieval layer, and it exists
because three implementations need it.
