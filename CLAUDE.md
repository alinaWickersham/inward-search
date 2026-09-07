# CLAUDE.md — working agreement for inward-search

This file governs how you work in this repository. Read it before every session.

## What this project is

inward-search is a semantic matching system for contemplative and wellbeing experiences. A person describes a felt state in plain language — "I've been running on empty and I want to be somewhere quiet" — and the system extracts structured intent, retrieves matching experiences, and surfaces trust and safety signals alongside the results.

The corpus is entirely synthetic. No real organisation, teacher, or business is ever named, characterised, or evaluated.

It is a public portfolio project. It will be read by hiring managers and engineers. It will also be defended in interviews by the repository owner, who must be able to explain every decision in it.

That last point governs everything below. Do not introduce anything the owner cannot explain. A clever abstraction she did not ask for and cannot justify is worse than a plain one she can.

## How to work

### Ask before you build

If a task is ambiguous, ask. Do not resolve ambiguity by picking something and proceeding. In particular, ask before:

* adding a dependency
* introducing an abstraction layer, base class, or framework
* changing the dimension schema
* restructuring directories
* adding configuration options nobody requested

### Explain the tradeoff, then recommend

When there is a real choice, state the options in two or three sentences each, say which you would pick, and say why. Do not present a decision as settled when it is not. Do not bury the choice in an implementation.

### Say when something is a bad idea

If asked to do something that will not work, will not scale to the stated scope, or contradicts a decision recorded in `docs/decisions/`, say so directly before doing it. Being agreeable is not the job.

### Scope discipline

Do what was asked. If you notice something else worth fixing, mention it and let the owner decide. Do not fix it in the same change.

## Code standards

Python 3.11+. Type hints on every function signature. Pydantic for anything crossing a boundary — LLM output, API input, stored records.

Plain over clever. This code will be read by strangers evaluating the author. A straightforward implementation of a well-chosen approach is the goal. No metaclasses, no dynamic dispatch, no decorators that hide control flow.

Functions do one thing and are short enough to read without scrolling.

No dead code. No commented-out blocks, no unused parameters "for later", no speculative interfaces with a single implementation.

Comments explain why, never what. `# offset-based so the original span can be restored` is useful. `# loop over listings` is noise. Delete noise.

Docstrings on modules and on any function whose purpose is not obvious from its name and signature. Say what it does and what the caller needs to know — not a restatement of the parameters.

Errors are handled where they can be handled. No bare `except:`. No swallowing exceptions to keep a script running unless the script is explicitly designed to continue past failures, and then log what failed.

Determinism where possible. Seed random operations. Record the model name and parameters used for any LLM call that produces stored data.

## Testing

Tests are required for:

* retrieval scoring and ranking
* metric calculations (recall@k, MRR, nDCG)
* intent extraction parsing and validation
* triage classification logic

Not required for: scripts that call the API to generate data, exploratory notebooks, the frontend.

Write tests that would catch a real regression. A test asserting that a function returns a non-empty list is not a test. Prefer a small number of tests with hand-computed expected values over many shallow ones.

`pytest`. Test files mirror source layout.

## Commits

Format:

```
<area>: <what changed, imperative, lower case>

<why, if not obvious from the diff — 1-3 sentences>
```

Areas: `corpus`, `retrieval`, `intent`, `triage`, `signals`, `eval`, `api`, `infra`, `docs`.

Good:

```
retrieval: weight structured dimensions above dense similarity

Near-duplicate pairs in the corpus differ on exactly one dimension, and
dense-only retrieval ranked both members identically. Structured match now
dominates when a dimension is explicitly constrained by the query.
```

```
eval: report triage false negatives separately from overall accuracy

Overall accuracy hides the only failure that matters here — missing a query
that needed support resources. Separate reporting makes the tradeoff visible.
```

Bad:

```
update files
fix bug
retrieval: add reranking          <- no why, and the diff is 200 lines
```

Rules:

* One logical change per commit. Not one file, not one session — one change.
* Never commit secrets, `.env`, or API keys. Check before every commit.
* Never commit generated artefacts that can be regenerated cheaply, except the corpus itself, which must be committed so results are reproducible.
* If the owner wrote the code by hand, do not add a co-author trailer.

## Decision records

Any decision that a reader might reasonably question gets a short record in `docs/decisions/NNNN-short-title.md`:

```markdown
# NNNN. <Decision>

Date: YYYY-MM-DD
Status: accepted | superseded by NNNN

## Context
What situation forced a choice.

## Decision
What was chosen.

## Alternatives considered
What else was on the table, and why it was not chosen.

## Consequences
What this makes easy. What it makes hard. What it rules out.
```

Decisions that need records include: the dimension schema and its size, the synthetic corpus, surface-not-gate in triage, Python over Go, the retrieval strategy comparison design, and any dependency that is hard to remove later.

Keep them short — half a page. Their value is that a reader can see the reasoning existed, not that it was exhaustive.

## Documentation

README must let a stranger understand and run the project. Required sections: what it is, why it exists, the synthetic-corpus statement, how to run it, how to reproduce the evaluation, and results with the honest caveats.

Never overstate. If the evaluation used one annotator and a synthetic corpus, say so plainly in the results section, not in a footnote. Understated and accurate reads as senior. Overstated reads as junior, and collapses the moment someone asks a follow-up question.

Every results table states what it cannot tell you.

## Safety and ethics constraints

These are not stylistic preferences. Do not relax them.

1. Synthetic corpus only. Never generate, ingest, or reference a real retreat centre, teacher, or organisation. Every listing carries `synthetic: true`. The README states this in the first paragraph.
2. Triage surfaces, never gates. No code path may remove, reorder, or withhold results based on an inferred mental state. Triage adds resources to a response. That is all it does.
3. No diagnostic language anywhere — not in code, comments, prompts, UI copy, or variable names. Never name or imply a condition. `possible_clinical_need` is a routing class, not an assessment, and nothing in the codebase may treat it as one.
4. Triage classifications are never persisted. Not to a database, not to logs, not to traces. If observability tooling would capture it, exclude it explicitly.
5. Trust signals describe, never conclude. "This listing does not name its teachers" is permitted. "This listing is untrustworthy" is not.
6. Crisis resources, if included, must be current and verified. If currency cannot be assured, do not hardcode them — say so and ask.

## What not to do

* Do not add a web framework, ORM, or dependency injection container.
* Do not build configuration systems for a project with one configuration.
* Do not write a plugin architecture. There are three retrieval strategies and there will be three.
* Do not generate long README sections of marketing prose. Plain description.
* Do not add emoji to code, commits, or documentation.
* Do not create files the owner did not ask for, including summary documents, status reports, or "next steps" notes.
* Do not claim in documentation that something is tested, validated, or measured unless it is.

## Current state

Update this section as the project moves.

* Phase 1 — corpus. In progress.
* Phases 2-4: retrieval baseline, intent extraction, hybrid comparison.
* Phases 5-6: triage, trust and contraindication signals.
* Phases 7-9: observability, deployment, write-up.

The minimum shippable project is the end of phase 4: corpus, three retrieval strategies, and the comparison table. Everything after that is depth.
