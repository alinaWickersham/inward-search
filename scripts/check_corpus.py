"""
Validate the corpus on disk.

    python scripts/check_corpus.py

Checks every file in corpus/listings/ parses as a Listing, every id in
corpus/plan.json has been generated, dimensions on disk match the plan,
and the near-duplicate pairs still differ on exactly the axis they should.
"""

import json
import sys

from threshold.corpus import CORPUS_DIR, load_listings, load_seeds


def main() -> int:
    problems: list[str] = []

    seeds = load_seeds()
    print(f"{len(seeds)} seeds OK")

    plan = {p["id"]: p for p in json.loads((CORPUS_DIR / "plan.json").read_text())}
    listings = {listing.id: listing for listing in load_listings()}
    print(f"{len(listings)} / {len(plan)} planned listings on disk")

    for lid, spec in plan.items():
        if lid not in listings:
            continue
        on_disk = listings[lid].dimensions.model_dump()
        if on_disk != spec["dimensions"]:
            problems.append(f"{lid}: dimensions on disk differ from plan")

    pairs: dict[str, list[dict]] = {}
    for spec in plan.values():
        if spec.get("pair"):
            pairs.setdefault(spec["pair"], []).append(spec)
    for pair_id, members in pairs.items():
        if len(members) != 2:
            problems.append(f"{pair_id}: expected 2 members, found {len(members)}")
            continue
        a, b = members
        diff = [k for k in a["dimensions"] if a["dimensions"][k] != b["dimensions"][k]]
        if diff != [a["varies_on"]]:
            problems.append(f"{pair_id}: differs on {diff}, should be only {a['varies_on']}")

    for p in problems:
        print("PROBLEM:", p, file=sys.stderr)
    print("corpus OK" if not problems else f"{len(problems)} problem(s)")
    return 1 if problems else 0


if __name__ == "__main__":
    sys.exit(main())
