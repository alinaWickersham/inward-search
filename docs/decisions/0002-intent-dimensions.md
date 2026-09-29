# 0002. Nine intent dimensions, categorical, required on listings and optional on queries

Date: 2026-09-07
Status: accepted

## Context

A felt-state query has to be matched against a listing. Both need a shared
representation. Changing that representation later means re-annotating the
whole corpus and the gold query set, so it has to be settled before
generation.

## Decision

Nine dimensions: social, structure, speech, guidance, physical demand,
tradition, experience level, duration, cost band. Each is a small enum of
three to six values rather than a continuous scale. Every listing has a
value on every dimension. A query has a value only where the person
expressed a preference; absence means "no preference", which is distinct
from a middle value.

Location is deliberately not a dimension. The problem being studied is
semantic matching over inner states; adding geography would make it a
travel-search problem with a semantic layer on top.

Accessibility (mobility, dietary, medical) is not a dimension either. It is
real and it interacts with the contraindication signals, but it is a
constraint on whether a person can attend, not a description of what they
are looking for. It lives in the `practical` text of a listing.

## Alternatives considered

**Continuous scales (0 to 1 per axis).** Finer matching, but a listing
cannot honestly be placed at 0.35 on "solitude"; the annotation would be
false precision, and an LLM extracting intent would produce arbitrary
numbers. Enums are what a human can annotate and defend.

**Fewer dimensions.** Simpler, but the phase 1 exercise of writing ten
realistic queries is the test: if a query cannot be expressed in the
dimensions, one is missing. Nine is the smallest set that has passed so far.

**Free-text only, no schema.** This is retrieval strategy A. It is kept as
the baseline the structured strategies are measured against, not as the
representation.

## Consequences

Listings and queries are directly comparable, and per-dimension extraction
accuracy is measurable. Near-duplicate listings differing on exactly one
axis become possible to construct. The cost is that anything the nine axes
do not capture is invisible to the structured strategies, which is part of
what the strategy comparison is designed to reveal.
