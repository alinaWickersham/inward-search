# 0001. The corpus is synthetic

Date: 2026-09-07
Status: accepted

## Context

The system annotates listings with trust and contraindication signals:
whether teachers are named, whether pricing is itemised, whether the
practice involves fasting or sleep restriction. Applying those labels to
real, named retreat centres is defamation territory, and real listing text
is copyrighted. The evaluation also needs listings that real directories do
not reliably contain: near-duplicate pairs differing on one dimension,
strong matches written badly, and listings with clear caution signals.

## Decision

Every listing is fictional, generated from a coverage plan and hand-edited.
Every listing carries `synthetic: true`, the loader refuses any file
without it, and the README says so in its first paragraph. No real
organisation, teacher, or business is named, characterised, or evaluated.

## Alternatives considered

**Scrape real listings.** Realistic prose for free, but copyrighted, and it
puts trust signals next to real names. Ruled out on legal grounds alone.

**Real listings with names removed.** Still copyrighted, still identifiable
from the text, and the corpus would have whatever coverage the internet
happened to have rather than the coverage the evaluation needs.

## Consequences

The evaluation can be designed rather than sampled, so it can discriminate
between retrieval strategies. The cost is that nothing here measures
performance on real listings or real users, and the write-up must say so
plainly in every results table.
