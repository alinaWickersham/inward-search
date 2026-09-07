"""
Coverage plan for the corpus.

A random spread of 120 listings would leave the evaluation unable to
discriminate between retrieval strategies. The corpus has to be *designed*:

  - broad spread, so ordinary queries have plausible matches
  - near-duplicate pairs differing on exactly one dimension, so a strategy
    that ignores that dimension is visibly punished
  - listings carrying trust and contraindication signals, for module 2
  - strong matches written badly, so lexical overlap and true relevance
    come apart

Run:  python scripts/coverage.py > corpus/plan.json
"""

import json
import random
from itertools import product

import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from schema import (
    Social, Structure, Speech, Guidance, PhysicalDemand,
    Tradition, ExperienceLevel, Duration, CostBand,
)

random.seed(11)   # reproducible corpus


# --------------------------------------------------------------------------

def spread(n=70):
    """Stratified spread. Walk tradition x duration x social so no corner of
    the space is empty, fill remaining dimensions randomly."""
    combos = list(product(list(Tradition), list(Duration), list(Social)))
    random.shuffle(combos)
    out = []
    for i in range(n):
        trad, dur, soc = combos[i % len(combos)]
        out.append({
            "kind": "spread",
            "dimensions": {
                "social": soc.value,
                "structure": random.choice(list(Structure)).value,
                "speech": random.choice(list(Speech)).value,
                "guidance": random.choice(list(Guidance)).value,
                "physical_demand": random.choice(list(PhysicalDemand)).value,
                "tradition": trad.value,
                "experience_level": random.choice(list(ExperienceLevel)).value,
                "duration": dur.value,
                "cost_band": random.choice(list(CostBand)).value,
            },
            "note": None,
        })
    return out


def near_duplicates(n_pairs=12):
    """Pairs identical except on one dimension. These are what make the
    evaluation able to tell strategies apart: an embedding-only approach
    will often rank both the same, a structured approach should not."""
    axes = ["social", "speech", "physical_demand", "structure",
            "guidance", "experience_level"]
    enums = {
        "social": Social, "speech": Speech, "physical_demand": PhysicalDemand,
        "structure": Structure, "guidance": Guidance,
        "experience_level": ExperienceLevel,
    }
    out = []
    for i in range(n_pairs):
        axis = axes[i % len(axes)]
        base = {
            "social": random.choice(list(Social)).value,
            "structure": random.choice(list(Structure)).value,
            "speech": random.choice(list(Speech)).value,
            "guidance": random.choice(list(Guidance)).value,
            "physical_demand": random.choice(list(PhysicalDemand)).value,
            "tradition": random.choice(list(Tradition)).value,
            "experience_level": random.choice(list(ExperienceLevel)).value,
            "duration": random.choice(list(Duration)).value,
            "cost_band": random.choice(list(CostBand)).value,
        }
        options = [e.value for e in enums[axis] if e.value != base[axis]]
        variant = dict(base)
        variant[axis] = random.choice(options)

        pair_id = f"pair{i:02d}"
        out.append({"kind": "near_dup", "pair": pair_id, "varies_on": axis,
                    "dimensions": base, "note": None})
        out.append({"kind": "near_dup", "pair": pair_id, "varies_on": axis,
                    "dimensions": variant, "note": None})
    return out


TRUST_NOTES = [
    "No individual teacher is named anywhere; the material refers only to 'our facilitators'.",
    "Pricing is described as an 'energy exchange' with a suggested range and language implying more is better.",
    "Participants are asked to surrender phones for the duration and contact with family is discouraged.",
    "The material centres on a single founder-teacher in devotional terms.",
    "Claims this is the only approach that addresses the true root of suffering.",
    "Newly established, no stated history, no named staff, no physical address.",
    "Long-established, teachers named with training listed, itemised pricing, clear cancellation terms.",
    "States an intake questionnaire and screening call before acceptance.",
    "Explicit about what the retreat is not, and who it is not suitable for.",
    "Fees itemised; scholarship process described with named administrator.",
]

CONTRA_NOTES = [
    "Includes a supervised three-day water fast.",
    "Sleep is restricted to four hours nightly as part of the practice.",
    "Extended holotropic-style breathwork sessions daily.",
    "Ten days of unbroken silence with no teacher check-ins.",
    "Twelve hours of seated practice daily.",
    "Ceremonial work with plant medicine, facilitated on site.",
    "Wilderness solo of four days with minimal food.",
    "Continuous practice through the night on several occasions.",
]


def signal_listings():
    """Listings carrying trust or contraindication signals."""
    out = []
    for note in TRUST_NOTES:
        out.append({
            "kind": "trust_signal",
            "dimensions": _random_dims(),
            "note": note,
        })
    for note in CONTRA_NOTES:
        d = _random_dims()
        d["physical_demand"] = PhysicalDemand.DEMANDING.value
        out.append({"kind": "contraindication", "dimensions": d, "note": note})
    return out


def awkward_prose(n=8):
    """Strong dimensional matches, badly written. Separates lexical overlap
    from real relevance — an important failure mode to be able to measure."""
    out = []
    for _ in range(n):
        out.append({
            "kind": "awkward",
            "dimensions": _random_dims(),
            "note": "Write this one poorly: clumsy phrasing, dated web-copy tone, "
                    "vague and repetitive, minor grammatical errors. The experience "
                    "itself should still be a genuinely good fit for its dimensions.",
        })
    return out


def _random_dims():
    return {
        "social": random.choice(list(Social)).value,
        "structure": random.choice(list(Structure)).value,
        "speech": random.choice(list(Speech)).value,
        "guidance": random.choice(list(Guidance)).value,
        "physical_demand": random.choice(list(PhysicalDemand)).value,
        "tradition": random.choice(list(Tradition)).value,
        "experience_level": random.choice(list(ExperienceLevel)).value,
        "duration": random.choice(list(Duration)).value,
        "cost_band": random.choice(list(CostBand)).value,
    }


def build_plan():
    plan = spread(70) + near_duplicates(12) + signal_listings() + awkward_prose(8)
    for i, item in enumerate(plan):
        item["id"] = f"L{i:03d}"
    return plan


if __name__ == "__main__":
    plan = build_plan()
    counts = {}
    for p in plan:
        counts[p["kind"]] = counts.get(p["kind"], 0) + 1
    print(json.dumps(plan, indent=2))
    print(f"\n// total: {len(plan)}  {counts}", file=__import__("sys").stderr)
