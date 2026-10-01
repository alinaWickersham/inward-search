import numpy as np

from tests.conftest import FakeModel, fake_vector, make_listing
from threshold.retrieval import embed


def test_listing_text_is_what_a_reader_sees_in_order() -> None:
    listing = make_listing("L1", "Stillwater House", summary="A quiet weekend.")
    assert embed.listing_text(listing) == (
        "Stillwater House\n\nA quiet weekend.\n\nStillwater House description"
        "\n\nStillwater House practical"
    )


def test_listing_text_does_not_depend_on_annotated_dimensions() -> None:
    # Strategy A must not see the structured labels.
    a = make_listing("L1", "Stillwater House", duration="hours", tradition="secular")
    b = make_listing("L1", "Stillwater House", duration="extended", tradition="yogic")
    assert embed.listing_text(a) == embed.listing_text(b)


def test_embed_listings_uses_passage_side_and_keeps_order(fake_model: FakeModel) -> None:
    listings = [make_listing("L1", "Pine Hollow"), make_listing("L2", "Ocean Hermitage")]
    matrix = embed.embed_listings(fake_model, listings)
    assert fake_model.calls == ["passage"]
    assert matrix.shape == (2, len(fake_vector("x")))
    np.testing.assert_array_equal(matrix[0], fake_vector(embed.listing_text(listings[0])))
    np.testing.assert_array_equal(matrix[1], fake_vector(embed.listing_text(listings[1])))


def test_embed_query_uses_query_side(fake_model: FakeModel) -> None:
    vector = embed.embed_query(fake_model, "somewhere quiet")
    assert fake_model.calls == ["query"]
    np.testing.assert_array_equal(vector, fake_vector("somewhere quiet"))
