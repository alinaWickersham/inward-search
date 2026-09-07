from threshold.corpus import load_seeds
from threshold.schema import Listing, QueryIntent


def test_seeds_validate_and_are_synthetic():
    seeds = load_seeds()
    assert len(seeds) == 3
    assert all(s.synthetic for s in seeds)


def test_query_intent_is_partial_by_default():
    intent = QueryIntent()
    assert all(v is None for v in intent.model_dump().values())


def test_listing_defaults_to_synthetic():
    seed = load_seeds()[0]
    data = seed.model_dump()
    data.pop("synthetic")
    assert Listing.model_validate(data).synthetic is True
