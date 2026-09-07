# Bridge project — specification

*Working title: **Threshold** (alternatives: Wayfinder, Stillpoint, Clearing)*

**A matching system for wellbeing experiences, with clinical safety constraints.**

---

## The premise

Every adjacent category has a default. Flights → Google Flights. Stays → Airbnb, Booking. Events → Eventbrite. Wellness classes → Mindbody. Spiritual and contemplative experiences → nothing. Retreat Guru, BookRetreats, and Insight Timer exist; none is the name that comes to mind.

There is a technical reason, and it is the reason this is worth building.

Every category above is served by **structured search**. Origin, destination, date, price. Location, dates, beds. The filters match how people decide.

Contemplative experiences do not work that way. Nobody thinks *"silent retreat, 5–7 days, under $2,000, within 200 miles."* They think *"I have been running on empty and I want to be somewhere quiet with people who will not ask me about work."*

That is a felt state, not a filter set. A conventional search UI cannot represent it. So the core problem is **semantic matching over described inner states** — structurally the same problem as matching a person to an appropriate form of care.

**Scope:** across traditions, weighted toward spiritual-but-not-religious — secular mindfulness, contemplative practice, nature-based retreats, yogic traditions, Buddhist-derived programs — rather than denominational religious programming.

---

## The problem underneath the problem

People search for retreats **because they are struggling**. "I have been running on empty and I need to get away from everything" is sometimes spiritual seeking and sometimes untreated depression. The words are identical.

Every existing product in this space ignores that distinction and sells the retreat.

That gap is what this project is actually about. Three things follow:

1. Some queries describe a state where a ten-day silent retreat is not the right answer, and may be actively harmful.
2. Some experiences carry documented risk for people with particular histories — and most listings say nothing about screening.
3. A system that quietly optimizes for booking will push people in exactly the wrong direction, and will look helpful doing it.

Building the version that handles this well is a mental health engineering problem that happens to use retreats as its corpus.

---

## What it does

1. A person describes their state in plain language.
2. **Triage** classifies what kind of need the query expresses.
3. **Intent extraction** parses the felt state into structured dimensions.
4. **Retrieval** finds and ranks matching experiences.
5. Each result carries an **explanation** of why it matched.
6. Each result carries **trust and contraindication signals**.
7. Where the query suggests clinical need, support resources are **surfaced alongside** results — never instead of, never as a gate.

Three modules:

- **Module 1 — Intent matching.** The technical core.
- **Module 2 — Trust and contraindication signals.** What a person should know before committing to an unregulated experience.
- **Module 3 — Triage and routing.** What the system does when the query suggests something other than seeking.

---

## Module 1: intent matching

### Intent dimensions

The design work is deciding what actually varies.

| Dimension | Range |
|---|---|
| Social | solitude ↔ community |
| Structure | fixed schedule ↔ self-directed |
| Speech | full silence ↔ dialogue-centred |
| Guidance | teacher-led ↔ self-guided |
| Physical demand | restful ↔ demanding |
| Tradition | secular, Buddhist-derived, yogic, contemplative Christian, nature-based, eclectic |
| Experience level | newcomer-friendly ↔ assumes practice |
| Duration | hours, weekend, week, longer |
| Cost band | free/donation, low, mid, high |

Each listing is annotated on the same dimensions. Each query is parsed into a partial specification — most will constrain only three or four.

### Pipeline

```
query (natural language)
  → triage classification             [Module 3]
  → intent extraction (LLM → Pydantic schema)
  → hybrid retrieval (dense embeddings + structured filters)
  → contraindication annotation        [Module 2]
  → reranking
  → explanation generation
  → response assembly (results + signals + resources)
```

### The headline experiment

Three retrieval strategies, compared on the same labeled query set:

- **A. Embedding-only.** Embed the raw query, cosine similarity against listing embeddings.
- **B. Structured-only.** Extract intent, filter and score on dimensions alone.
- **C. Hybrid.** Structured intent constrains and weights dense retrieval.

**The question:** does decomposing a felt-state query into structured dimensions actually beat throwing it at an embedding model?

Genuinely open, not obvious, and directly relevant to anyone building semantic search over subjective preferences — including therapist matching at a mental health company.

---

## Module 2: trust and contraindication signals

Retreats are largely unregulated. Some involve fasting, sleep restriction, intense breathwork, or psychedelics. A small number of communities are coercive. There is no trustworthy review layer.

### Trust signals

**Positive / neutral**

- Years in operation
- Named teachers with stated, checkable background
- Transparent, itemized pricing
- Stated screening or intake process
- Clear arrival and departure terms

**Caution**

- Practices carrying physical risk (extended fasting, sleep restriction, prolonged breathwork)
- Pressure language around donations or "energy exchange"
- Discouragement of outside contact during the experience
- Devotional framing around a single leader
- Claims of exclusive access to truth or healing
- No named individuals anywhere in the material

### Contraindication signals

Grounded in the published literature on adverse effects of intensive contemplative practice — Britton and colleagues at Brown are the anchor for the meditation adverse-effects work. Cite specific sources in the repo rather than gesturing at "research."

Documented risk factors include trauma history, psychosis vulnerability, dissociative symptoms, and active eating disorders, particularly against prolonged silence, extended retreats, fasting, and intensive breathwork.

The system matches **fit and risk together**: this experience matches what you described, *and* here is what its own materials say about screening — or the fact that they say nothing.

**Output is descriptive, never a verdict.** "This listing does not name its teachers." Not "this is a cult." The product surfaces what is present and absent; the reader decides.

Technically this is text classification over defined categories with a labeled evaluation set — and the natural place to **train a small classifier** rather than prompting for everything.

---

## Module 3: triage and routing

### The design principle

**Surface, never gate.** The system notices signals, says what it noticed, offers a path, and gets out of the way. A person who reads a suggestion to talk to someone and still wants the retreat gets the retreat.

This is not softness. A system that blocks results based on an inferred mental state is making a clinical judgment it is not qualified to make, on evidence it does not have, about a person it cannot see. Preserving choice is the correct design, not a compromise.

### Classification

| Class | Response |
|---|---|
| **Seeking** | Normal results. |
| **Stress / burnout** | Normal results, weighted toward restful and supported experiences. |
| **Possible clinical need** | Results, plus a clearly separated note offering support resources. |
| **Acute risk** | Support resources first and prominently. Results still shown below, unfiltered. |

Deliberately conservative on the *response* side and unaggressive on the *filtering* side: the system escalates what it offers, never what it withholds.

### What it never does

- Name a condition, or imply one.
- Score or rate the person.
- Remove or reorder results based on inferred mental state.
- Store the classification.
- Use assessment language ("you appear to be…").

### Spiritual bypassing

A recognized phenomenon: using spiritual practice to avoid psychological material. Relevant because it is the failure mode this system could actively worsen. Handled through the same mechanism — where a query suggests avoidance rather than seeking, the system offers the other option alongside, never in place of.

**Building a recommender willing to not recommend** is an unusual thing to have done, and it demonstrates exactly the judgment about where AI helps versus adds risk that these roles ask for.

---

## Corpus

**80–120 synthetic listings**, written to mirror the structure, tone, and range of real ones found online, and **clearly labeled as synthetic** throughout the repo and UI.

Deliberate, not a shortcut:

- Applying risk or trust signals to real, named retreat centers is legally and ethically hazardous.
- Real listings are copyrighted text.
- A synthetic corpus can be designed to cover the dimension space evenly, including the edge cases that make evaluation meaningful — near-duplicates differing on one dimension, strong matches that are badly written, listings with clear caution signals.

Generate from a coverage matrix you define, then hand-edit for realism. Budget one weekend.

---

## Evaluation

This is what makes it evidence rather than a demo.

**Query set.** ~50 natural-language queries phrased as real people would, hand-labeled with relevant listings *and* a gold triage class.

| Area | Measures |
|---|---|
| Retrieval | recall@5, recall@10, MRR, nDCG across strategies A/B/C |
| Intent extraction | per-dimension accuracy against gold intents |
| Trust and contraindication classification | precision and recall per signal category |
| **Triage** | **precision and recall per class, with false negatives on the two highest-need classes reported separately — this is the number that actually matters** |
| Cost and latency | per query, per strategy |

**Reported as:** a comparison table across strategies, a per-dimension breakdown of where intent extraction fails, a triage confusion matrix, and an honest section on what the evaluation cannot tell you — synthetic corpus, single annotator, no real users, no clinical validation.

That honesty section separates someone who ran an eval from someone who understands evaluation.

---

## Legal posture

*Not legal advice — this is the shape of the problem. A lawyer draws the actual lines if it ever becomes real.*

**As a portfolio project, exposure is minimal**, and the design choices already made are why: synthetic corpus, no real business characterized, nothing deployed as a service to real users, no clinical claims.

**If it ever became real**, the issues to take seriously:

- **Not medical advice.** Prominent and unavoidable, reflected in interface language rather than buried in a footer.
- **No diagnosis, no assessment.** Vocabulary matters. "Some people find it helpful to talk to someone" is a suggestion. "You appear to be experiencing depression" is a clinical claim, and in many states, unlicensed practice.
- **Surface, never gate.** Withholding results based on inferred mental state creates a duty you cannot discharge. Offering resources does not.
- **Characterizing real businesses is the biggest risk** — larger than the health angle. Trust signals applied to a named retreat center is defamation territory. If it went live: verifiable facts only, everything sourced, a correction path for operators, and counsel first.
- **Crisis resources must be current and correct.** Wrong numbers are worse than none.
- **Terms of service and professional liability insurance** before any real user touches it.

Documenting this reasoning in the repo is itself part of what the project demonstrates. Most portfolio projects show no evidence anyone thought about liability at all.

---

## Stack

| Layer | Choice | Why |
|---|---|---|
| Orchestration | LangGraph | Agentic pipeline, legible as a state graph |
| Schemas | Pydantic | Typed intent, signal, and triage outputs |
| Store | PostgreSQL + pgvector | Dense retrieval and structured filters in one place |
| Tracing | Langfuse | Latency, tokens, cost, scores per trace |
| API | FastAPI | Standard, testable |
| Classifier | scikit-learn or a small fine-tune | One trained model rather than all prompting |
| Frontend | Minimal React or plain HTML | Enough to demo; not the point |
| Packaging | Docker | — |
| Deployment | k3s on a single EC2 instance | Kubernetes exposure at near-zero cost |
| Models | Two or three, at least one open-weight | Comparison, and cost realism |

---

## Milestones

Ship something at every stage.

**Weekend 1 — corpus.** Coverage matrix, generate and hand-edit 80–120 listings, annotate on the intent dimensions.

**Weekend 2 — retrieval baseline.** Embeddings in pgvector, strategy A end to end from a CLI. *Write the scoring and metrics code by hand, unassisted — this doubles as interview practice.*

**Weekend 3 — intent extraction.** Pydantic schema, LLM extraction, strategy B. Hand-label the 50-query gold set including triage classes.

**Weekend 4 — hybrid and comparison.** Strategy C, full metrics run, first comparison table. **Minimum shippable project.** If life intervenes, stop here and write it up.

**Weekend 5 — triage.** Classification, routing behavior, response assembly. Triage evaluation with false negatives reported separately.

**Weekend 6 — trust and contraindications.** Signal taxonomy grounded in the literature, extraction, labeled evaluation. Train a small classifier for one category.

**Weekend 7 — observability and API.** Langfuse tracing, cost and latency tracking, FastAPI wrapper.

**Weekend 8 — deploy.** Docker, k3s on EC2, minimal frontend, README a stranger can follow.

**Weekend 9 — write it up.** Report, charts, legal-posture note, published on the site and the repo.

---

## What it demonstrates

| Requirement | Where it shows |
|---|---|
| RAG, embeddings, vector search | Retrieval pipeline, pgvector |
| Agentic systems and orchestration | LangGraph state graph |
| Evaluating complex AI systems, actionable hypotheses | Three-strategy comparison, triage evaluation |
| Custom model training | Contraindication classifier |
| Data analysis and visualization | Metrics tables, confusion matrix, charts |
| Kubernetes and cloud deployment | k3s on EC2 |
| Cost and latency awareness | Langfuse instrumentation |
| Architecting modular, reusable systems | Pluggable strategies, swappable corpus |
| **Judgment about where AI helps vs adds risk in a healthcare context** | **Module 3 in full — design, constraints, and documented reasoning** |
| Responsible handling of sensitive data | No storage of triage classifications; synthetic corpus |

---

## The interview sentence

> *I built a matching system for wellbeing experiences. The technical core is semantic matching over described inner states — turning "I have been running on empty" into structured intent and retrieving against it. The harder part was what to do when a query suggests clinical need rather than spiritual seeking, because the words are the same. So there is a triage layer that surfaces support resources without ever gating results, and a contraindication layer grounded in the adverse-effects literature. The evaluation reports false negatives on the high-need classes separately, because that is the number that actually matters.*

That is the same problem as matching a member to appropriate care, and it says so without you having to argue it.
