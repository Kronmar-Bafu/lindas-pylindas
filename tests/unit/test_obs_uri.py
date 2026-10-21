"""Property-based tests for observation URI construction.

Covers the pure static helper ``Cube._make_obs_iri`` which builds an
observation IRI from a cube URI and an ordered list of key-dimension values by
percent-encoding each value (``quote(..., safe="")``), joining them with ``_``,
and wrapping the result in a ``URIRef``.

Validates: Requirements 15.1, 15.2, 15.3, 15.4
"""

from urllib.parse import quote

from hypothesis import given, settings
from hypothesis import strategies as st
from rdflib import URIRef

from pylindas.pycube.cube import Cube


CUBE_URI = "https://example.org/cube/1"


# Feature: pylindas-modernization, Property 9: Observation URI construction
@settings(max_examples=100)
@given(key_values=st.lists(st.text(), min_size=1, max_size=5))
def test_make_obs_iri_matches_quoted_underscore_join(key_values):
    """For any non-empty list of key values (including reserved URI chars),
    the observation IRI equals the cube URI + ``/observation/`` + the values
    percent-encoded and joined by ``_``, returned as a ``URIRef``.
    """
    result = Cube._make_obs_iri(CUBE_URI, key_values)

    expected = URIRef(
        f"{CUBE_URI}/observation/"
        + "_".join(quote(str(v), safe="") for v in key_values)
    )

    # Pins percent-encoding of reserved chars, the ``_`` join order, the
    # ``/observation/`` literal, and the URIRef type all at once.
    assert result == expected
    assert isinstance(result, URIRef)

    # Single-element lists introduce no join underscore: the segment after
    # ``/observation/`` is exactly the quoted value (which may itself contain
    # an underscore, hence the comparison against the computed quoted value).
    if len(key_values) == 1:
        suffix = str(result)[len(f"{CUBE_URI}/observation/"):]
        assert suffix == quote(str(key_values[0]), safe="")
