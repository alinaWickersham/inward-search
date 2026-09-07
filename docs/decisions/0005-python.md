# 0005. Python

Date: 2026-09-07
Status: accepted

## Context

The project needs an LLM client, typed schemas for model output, a vector
store client, an orchestration layer, a small trained classifier, and an
evaluation harness. It is built in spare time by one person, and it will be
read by others.

## Decision

Python 3.11 or later throughout. Pydantic for every boundary: LLM output,
API input, stored records.

## Alternatives considered

**Go.** Better for a long-running service, and a reasonable choice for the
API layer alone. But every other piece, from the LLM SDKs to scikit-learn
to LangGraph, is Python-first, and a Go service would need a Python
sidecar for the classifier and the evaluation anyway. Two languages for a
project this size is a cost with no finding attached.

**TypeScript.** The LLM tooling is good, the ML tooling is not. The trained
classifier and the metrics work would be fighting the ecosystem.

## Consequences

Everything lives in one language and one package. Structured LLM output
validates at the boundary instead of being trusted. The cost is that the
API layer is slower and heavier than it would be in Go, which does not
matter at this scale and would be revisited if it ever did.
