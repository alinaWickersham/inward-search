# 0008. The gold set is labelled on a pool, with binary relevance and any-of intents

Date: 2026-10-01
Status: accepted

## Context

The three-strategy comparison needs a gold set: queries with hand-labelled
intent, triage class, and relevant listings. One person labels it. Judging
all 120 listings for every query would be about 6,000 judgements, and the
labelling has to be easy enough to actually finish.

## Decision

- Queries are written by the owner, in her own voice, typos kept. One JSON
  file per query in `eval/gold/`, committed like the corpus.
- Relevance is binary: relevant or not.
- Each query is judged on a pool: strategy A's top 20, every listing that
  matches the gold intent on all the dimensions it constrains, and the
  near-duplicate partner of anything in the pool. Unjudged listings count as
  not relevant. The pool is shown in a seeded shuffle, and listings are shown
  as text without their annotations, so the labeller sees neither A's ranking
  nor the labels that B would match on.
- The gold intent allows several values per dimension ("a weekend or a
  week"). Extraction counts as correct if it picks any of them.
- The gold triage class is stored. These are labels on queries the owner
  wrote, not a classification of a person, so constraint 4 in CLAUDE.md
  (never persist triage classifications) does not apply to them. Runtime
  classifications of real input remain unstored.
- Labelling happens in a local page (`label.html`) served by a separate app
  with write routes; the search app has none.

## Alternatives considered

**Judge all 120 per query.** No pooling bias, but too slow to finish.

**Pool from A only.** Fewer judgements, but every relevant listing A missed
would count as irrelevant, which would flatter A against B and C.

**Graded relevance (0/1/2).** Makes nDCG more informative, but slower to
decide; binary was chosen for speed. nDCG on binary labels still rewards
ranking relevant listings higher.

**Single-valued gold intent.** Matches `QueryIntent`, but cannot represent
queries that genuinely allow two values, and would mark a correct
extraction wrong.

## Consequences

Labelling is a few hundred keypresses per query rather than 120 reads. The
pool still leans toward A and toward the structured match on the gold
intent; a relevant listing that neither finds is never judged. The results
section must say so. When B and C exist, their top results should be added
to the pools and judged before the final comparison, so no strategy is
scored against listings nobody looked at. `QueryIntent` is single-valued
while the gold intent is not; phase 3 extraction has to decide whether to
predict one value or several.
