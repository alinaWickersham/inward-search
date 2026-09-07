"""
Corpus loader.

Every listing in this corpus is SYNTHETIC. The `synthetic` flag on
`Listing` defaults to True and the loader refuses any file that sets it
to False — see corpus/README.md for why.
"""

import json
from pathlib import Path

from threshold.schema import Listing

# <repo>/corpus — the package lives in src/threshold/, so go up three levels.
CORPUS_DIR = Path(__file__).resolve().parents[3] / "corpus"


def _read(path: Path) -> Listing:
    data = json.loads(path.read_text())
    listing = Listing.model_validate(data)
    if not listing.synthetic:
        raise ValueError(f"{path.name}: listing is not marked synthetic; refusing to load")
    return listing


def load_seeds(corpus_dir: Path = CORPUS_DIR) -> list[Listing]:
    """The hand-written listings that set the register for generation."""
    return [Listing.model_validate(s) for s in json.loads((corpus_dir / "seeds.json").read_text())]


def load_listings(corpus_dir: Path = CORPUS_DIR) -> list[Listing]:
    """All generated listings in corpus/listings/, sorted by id."""
    files = sorted((corpus_dir / "listings").glob("*.json"))
    return [_read(f) for f in files]
