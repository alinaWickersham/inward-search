# Phase 1 — the corpus

Goal for this phase: **120 annotated synthetic listings on disk**, and a
dimension schema you are confident enough in to build the next five phases on.

---

## Why this phase matters more than it looks

Changing a dimension later means re-annotating 120 listings and rewriting the
gold query set. So the real work in this phase is not generation — it is
**deciding whether the nine dimensions are right**. Generation is a script.

Before you run anything, do this: write ten queries the way a real person
would phrase them. Not "silent retreat under $1000" — write *"I want to go
somewhere I won't have to talk to anyone for a few days"* and *"something
structured, I don't do well with unstructured time"* and *"I've never
meditated and I don't want to be the only beginner."*

Then check: **can each query be expressed in the nine dimensions?** If one
cannot, you are missing a dimension. If a dimension never appears in ten
queries, it may not earn its place.

Two I already suspect are missing and worth deciding on now:

- **Location / travel distance.** Deliberately left out to keep the matching
  problem semantic rather than geographic. Defensible, but decide it on
  purpose.
- **Accessibility** — mobility, dietary, medical. Real and important, and it
  interacts with module 2. Might belong in `practical` rather than as a
  matched dimension.

---

## The ten queries

Written before generation, as the check on the schema. Kept as typed, typos
included, because that is what the intent extractor will see. The first six
were written by the owner; the last four were added to reach dimensions the
first six did not touch.

1. *im on maui in the end of august, i will stay in paia in a hostel and im
   not palnning to rent a car, recommend spiritual activities like meditation*
2. *im on maui and i am on a budget, i want free activiites to do while on
   vacation*
3. *i feel tired and slightly burnt out, anything in the area i could do to
   help myself?*
4. *inormally cope with alcohol and i know im an alcoholic and i need help, my
   therapist said i need to be more mindful, what can i do in richmond va*
5. *i have done a 10 day silent meditation retreat and practice meditation and
   yoga somewhat reguallry, i wnt to deepen my sprituality and i want to try
   next level and maybe do ayauska or advanced meditation/yoga somewhere in
   the US*
6. *too much going on lately - pet passing, constant house maintenance issues
   and expenses - i need to ground and center*
7. *i want to go somewhere i won't have to talk to anyone for a few days. not
   a group thing, not a class*
8. *never meditated. i don't want to be the only beginner in the room and i
   need an actual schedule, i don't do well with unstructured time*
9. *something christian but contemplative, not a church service. a quiet
   weekend, some guidance but not someone talking at me the whole time*
10. *outdoors, lots of walking, a week or so with other people. not interested
    in sitting still for hours*

### What each query constrains

Only dimensions the query actually expresses. Blank means no preference,
which is a valid and common state.

| # | social | structure | speech | guidance | physical | tradition | experience | duration | cost |
|---|---|---|---|---|---|---|---|---|---|
| 1 | | | | | | | | hours | |
| 2 | | | | | | | | hours | free_or_donation |
| 3 | | | | light_guidance | restful | | | | |
| 4 | | | | teacher_led | | secular | newcomer_friendly | hours | |
| 5 | | | | | demanding | eclectic | assumes_practice | week or extended | |
| 6 | | | | | restful | | | | |
| 7 | solitude | self_directed | full_silence | self_guided | | | | weekend or week | |
| 8 | small_group or community | fixed | | teacher_led | | | newcomer_friendly | | |
| 9 | | | partial_silence | light_guidance | | contemplative_christian | | weekend | |
| 10 | small_group or community | | | | demanding | nature_based | | week | |

Every dimension is constrained by at least one query, and no query needs a
dimension that does not exist. The nine hold.

Queries 3, 4, and 6 also carry the kind of signal the triage layer is for.
That is labeled in phase 3, not here.

### What the queries mention that is not a dimension

Four of the ten name a place (Maui, Paia, Richmond, "the US", "in the area").
One names a month, one says no car, and one names a substance whose
listings will carry a contraindication signal. Place, dates, and transport
are deliberately not dimensions (decision 0002): the problem under study is
matching the described state, not the geography. The extractor is expected
to read past them. The contraindication is module 2 material and belongs
on the listing, not in the query intent.

Accessibility (mobility, dietary, medical) was considered and left out. It
lives in the `practical` text of a listing.

## Files

```
src/threshold/
  schema.py            dimensions, Listing, QueryIntent, TriageClass
  corpus/loader.py     loads seeds + listings, refuses anything not marked synthetic
corpus/
  seeds.json           3 hand-written listings that set the register
  plan.json            generated: 120 listing specs
  listings/            one JSON per listing, written from the plan
scripts/
  coverage.py          builds plan.json
  check_corpus.py      validates listings/ against plan.json and the schema
```

## The plan, as generated

| Kind | Count | Purpose |
|---|---|---|
| `spread` | 70 | Stratified across tradition × duration × social, so ordinary queries have plausible matches |
| `near_dup` | 24 (12 pairs) | Identical except one dimension — this is what lets the evaluation tell strategies apart |
| `trust_signal` | 10 | Module 2 material, positive and cautionary |
| `contraindication` | 8 | Intensive practices with documented risk |
| `awkward` | 8 | Good dimensional matches, badly written — separates lexical overlap from real relevance |

The near-duplicate pairs are the cleverest part and worth understanding. If
two listings differ only in `speech`, and a query says *"I don't want to talk
to anyone"*, then a strategy that ranks both equally is demonstrably failing
at something a structured strategy should get right. Without these pairs, all
three strategies will look about the same and you will have no finding.

---

## How the listings were written

The plan fixes the dimensions, kind, and notes for each of the 120 listings.
The listings themselves were written from it by a Claude model working in a
Claude Code session, one file per plan entry, against the three seeds for
register. An API script was considered and dropped: it would have written
each listing independently, and the near-duplicate pairs need to be written
together so that the two members are genuinely confusable in prose and differ
only where the plan says they differ.

Each listing carries a `generation` block naming the model that wrote it and
the plan entry it was written from.

```bash
pip install -e ".[dev]"
python scripts/coverage.py > corpus/plan.json     # rebuild the plan if coverage.py changes
python scripts/check_corpus.py                    # every file parses and matches the plan
```

---

## Read them

Do not skip this. Open twenty at random and check:

- **Does it read as its dimensions?** A listing marked `solitude` should feel
  solitary without saying "this is a solitary retreat." If you cannot tell,
  the annotation is a lie and the evaluation is measuring nothing.
- **Does it sound like a person?** Model-written listings drift toward wellness
  advertising. The seeds push against that; some will still slip.
- **Are the near-duplicate pairs genuinely close?** They should be plausibly
  confusable in prose while differing on exactly one axis.
- **Any real organisation names?** There should be none. Grep for anything
  that sounds like a real centre and rewrite it.

Hand-edit freely. A corpus you have read and corrected is worth more than a
larger one you have not.

---

## Definition of done

- [x] Ten realistic queries written by hand
- [x] Nine dimensions confirmed against those queries, or amended
- [x] `plan.json` generated
- [ ] 120 listings written
- [ ] Twenty read and corrected by hand
- [ ] No real organisation names anywhere
- [x] Committed to a repo, with a README that says the corpus is synthetic and why
