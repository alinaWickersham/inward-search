import json
import runpy
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def test_plan_on_disk_matches_generator():
    """coverage.py is seeded; the committed plan must be reproducible."""
    module = runpy.run_path(str(ROOT / "scripts" / "coverage.py"), run_name="not_main")
    fresh = module["build_plan"]()
    on_disk = json.loads((ROOT / "corpus" / "plan.json").read_text())
    assert fresh == on_disk


def test_plan_composition():
    plan = json.loads((ROOT / "corpus" / "plan.json").read_text())
    kinds = {}
    for p in plan:
        kinds[p["kind"]] = kinds.get(p["kind"], 0) + 1
    assert len(plan) == 120
    assert kinds == {"spread": 70, "near_dup": 24, "trust_signal": 10,
                     "contraindication": 8, "awkward": 8}
