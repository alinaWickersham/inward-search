"""
Generate the listing corpus from the coverage plan.

    export ANTHROPIC_API_KEY=...
    python scripts/generate.py --limit 5          # try a few first
    python scripts/generate.py                    # the full 120

Writes one JSON file per listing to corpus/listings/, so a crashed run
resumes instead of starting over and you never pay twice for the same
listing.

Expect roughly $5-15 for the full corpus depending on model.
"""

import argparse
import json
import sys
from pathlib import Path

import anthropic

ROOT = Path(__file__).resolve().parent.parent

MODEL = "claude-sonnet-4-6"
OUT = ROOT / "corpus" / "listings"

SYSTEM = """You write listings for a directory of contemplative and spiritual \
experiences. Every listing you produce is FICTIONAL and is used to test a search \
system. Never use the name of a real retreat centre, teacher, or organisation.

Write the way real operators write: specific, plain, occasionally awkward. Real \
listings are not marketing copy. They mention the composting toilet and the eleven \
miles to town. They say what the place is not. Avoid the register of wellness \
advertising — no "journey", no "sacred container", no "transformative", unless the \
listing is deliberately meant to sound like that.

Invent place names and regions that sound real but are not identifiable \
organisations. Real geography (a county, a range of hills) is fine.

Return ONLY a JSON object, no preamble, no markdown fence."""

TEMPLATE = """Write one listing with exactly these dimension values:

{dims}

Dimension meanings:
- social: solitude (alone) / small_group (under ~15) / community (larger)
- structure: fixed (published schedule, attendance expected) / semi_structured \
(anchor sessions, free time) / self_directed (you decide)
- speech: full_silence / partial_silence (silent periods) / dialogue (talking is the point)
- guidance: teacher_led / light_guidance (available, not constant) / self_guided
- physical_demand: restful / moderate / demanding (long sits, long hikes, early starts)
- tradition: secular / buddhist_derived / yogic / contemplative_christian / \
nature_based / eclectic
- experience_level: newcomer_friendly / some_experience / assumes_practice
- duration: hours / weekend / week / extended (longer than a week)
- cost_band: free_or_donation / low / mid / high

{note}

The listing must be *readable as* those dimensions without naming them. A reader \
should be able to infer "this is solitary" from the description, not from a label.

Return JSON with exactly these keys:
  name        - the place or programme name
  location    - invented place, real region
  summary     - one or two sentences, as a directory would show
  description - 150-350 words, the operator's own voice
  practical   - dates, cost, what's included, what to bring, access notes
"""


def load_seeds():
    seeds = json.loads((ROOT / "corpus" / "seeds.json").read_text())
    parts = []
    for s in seeds:
        parts.append(json.dumps({
            "name": s["name"], "location": s["location"],
            "summary": s["summary"], "description": s["description"],
            "practical": s["practical"],
        }, indent=2))
    return (
        "Here are three examples of the register to write in. Match their level of "
        "specificity and their lack of marketing language.\n\n" + "\n\n".join(parts)
    )


def build_prompt(item, seed_block):
    note = ""
    if item.get("note"):
        note = f"Additional requirement for this listing:\n{item['note']}\n"
    return (
        seed_block
        + "\n\n---\n\n"
        + TEMPLATE.format(
            dims=json.dumps(item["dimensions"], indent=2),
            note=note,
        )
    )


def generate(client, item, seed_block):
    resp = client.messages.create(
        model=MODEL,
        max_tokens=1500,
        system=SYSTEM,
        messages=[{"role": "user", "content": build_prompt(item, seed_block)}],
    )
    text = "".join(b.text for b in resp.content if b.type == "text").strip()
    if text.startswith("```"):
        text = text.split("```")[1]
        if text.startswith("json"):
            text = text[4:]
    data = json.loads(text)

    return {
        "id": item["id"],
        "name": data["name"],
        "location": data["location"],
        "summary": data["summary"],
        "description": data["description"],
        "practical": data["practical"],
        "dimensions": item["dimensions"],
        "kind": item["kind"],
        "pair": item.get("pair"),
        "varies_on": item.get("varies_on"),
        "generation_note": item.get("note"),
        "synthetic": True,
    }


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--limit", type=int, default=None)
    ap.add_argument("--force", action="store_true", help="regenerate existing")
    args = ap.parse_args()

    OUT.mkdir(parents=True, exist_ok=True)
    plan = json.loads((ROOT / "corpus" / "plan.json").read_text())
    seed_block = load_seeds()
    client = anthropic.Anthropic()

    todo = plan[: args.limit] if args.limit else plan
    for item in todo:
        path = OUT / f"{item['id']}.json"
        if path.exists() and not args.force:
            continue
        try:
            listing = generate(client, item, seed_block)
        except Exception as e:                      # noqa: BLE001
            print(f"  {item['id']} FAILED: {e}", file=sys.stderr)
            continue
        path.write_text(json.dumps(listing, indent=2))
        print(f"  {item['id']}  {listing['name']}")

    print(f"\n{len(list(OUT.glob('*.json')))} listings in {OUT}")


if __name__ == "__main__":
    main()
