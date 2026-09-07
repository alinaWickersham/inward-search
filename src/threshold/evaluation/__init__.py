"""
Evaluation (weekends 2–6).

Retrieval:   recall@5, recall@10, MRR, nDCG across strategies A/B/C
Intent:      per-dimension accuracy against gold intents
Signals:     precision / recall per signal category
Triage:      precision / recall per class, with false negatives on the two
             highest-need classes reported separately — the number that
             actually matters
Cost:        tokens, latency, and cost per query per strategy

Gold labels live in evaluation/queries/. Run outputs go to evaluation/runs/
(gitignored).

Metrics code is written by hand, without assistance — see the spec.
"""
