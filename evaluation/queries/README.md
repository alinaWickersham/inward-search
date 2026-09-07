# Gold query set (weekend 3)

~50 natural-language queries, phrased the way real people phrase them, each
hand-labeled with:

- the listing ids that are relevant (for recall@k, MRR, nDCG)
- a gold `QueryIntent` (for per-dimension extraction accuracy)
- a gold `TriageClass` (for triage precision/recall)

Format to be fixed in weekend 3. Run outputs go to `evaluation/runs/`, which
is gitignored.

Known limits, to be repeated in the write-up: single annotator, synthetic
corpus, no real users, no clinical validation.
