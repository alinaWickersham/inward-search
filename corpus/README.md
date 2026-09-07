# Corpus — synthetic, by design

**Every listing in this directory is fictional.** The places, programmes,
teachers, and organisations do not exist. Any resemblance to a real retreat
centre is coincidental, and if you find one, open an issue so it can be
regenerated.

This is deliberate, not a shortcut:

- Applying trust or contraindication signals to real, named retreat centres
  is legally and ethically hazardous.
- Real listings are copyrighted text.
- A synthetic corpus can be designed to cover the dimension space evenly,
  including the edge cases that make evaluation meaningful.

## Contents

| File | What |
|---|---|
| `seeds.json` | Three hand-written listings that set the register for generation |
| `plan.json` | 120 listing specifications, generated deterministically by `scripts/coverage.py` |
| `listings/` | One JSON file per generated listing, `L000.json` … `L119.json` |

## Composition of the plan

| Kind | Count | Purpose |
|---|---|---|
| `spread` | 70 | Stratified across tradition × duration × social, so ordinary queries have plausible matches |
| `near_dup` | 24 (12 pairs) | Identical except on one dimension — what lets the evaluation tell strategies apart |
| `trust_signal` | 10 | Module 2 material, positive and cautionary |
| `contraindication` | 8 | Intensive practices with documented risk |
| `awkward` | 8 | Good dimensional matches, badly written — separates lexical overlap from real relevance |

Every listing carries `"synthetic": true`. The loader in
`threshold.corpus` refuses to load a file without it.
