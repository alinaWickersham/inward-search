# Weekend 1 — the corpus

Goal by Sunday night: **120 annotated synthetic listings on disk**, and a
dimension schema you are confident enough in to build the next five weekends on.

---

## Why this weekend matters more than it looks

Changing a dimension later means re-annotating 120 listings and rewriting the
gold query set. So the real work this weekend is not generation — it is
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

## Files

```
src/threshold/
  schema.py            dimensions, Listing, QueryIntent, TriageClass
  corpus/loader.py     loads seeds + listings, refuses anything not marked synthetic
corpus/
  seeds.json           3 hand-written listings that set the register
  plan.json            generated: 120 listing specs
  listings/            generated: one JSON per listing
scripts/
  coverage.py          builds plan.json
  generate.py          builds listings/ from plan.json
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

## Run order

```bash
pip install -e ".[corpus,dev]"
export ANTHROPIC_API_KEY=...

python scripts/coverage.py > corpus/plan.json     # free, instant
python scripts/generate.py --limit 5              # ~$0.50, check the output
python scripts/generate.py                        # ~$5-15, the rest
python scripts/check_corpus.py                    # every file parses, matches the plan
```

`generate.py` writes one file per listing and skips what already exists, so a
crash resumes rather than restarting, and you never pay twice.

---

## After generation: read them

Do not skip this. Open twenty at random and check:

- **Does it read as its dimensions?** A listing marked `solitude` should feel
  solitary without saying "this is a solitary retreat." If you cannot tell,
  the annotation is a lie and the evaluation is measuring nothing.
- **Does it sound like a person?** Generated listings drift toward wellness
  advertising. The seeds push against that; some will still slip.
- **Are the near-duplicate pairs genuinely close?** They should be plausibly
  confusable in prose while differing on exactly one axis.
- **Any real organisation names?** There should be none. Grep for anything
  that sounds like a real centre and regenerate it.

Hand-edit freely. A corpus you have read and corrected is worth more than a
larger one you have not.

---

## Definition of done

- [ ] Ten realistic queries written by hand
- [ ] Nine dimensions confirmed against those queries, or amended
- [ ] `plan.json` generated
- [ ] 120 listings generated
- [ ] Twenty read and corrected by hand
- [ ] No real organisation names anywhere
- [ ] Committed to a repo, with a README that says the corpus is synthetic and why

---

## Note on the API key

`generate.py` reads `ANTHROPIC_API_KEY` from the environment. Do not put a key
in a file that could be committed. Add `.env` and `corpus/listings/` decisions
to `.gitignore` deliberately — listings should probably be committed, since
someone reproducing your results needs them.
