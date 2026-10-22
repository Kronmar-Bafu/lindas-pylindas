"""Property-based tests for base-URI normalization and cube URI construction.

Design reference: Pylindas Modernization — Requirement 12 (base-URI
normalization and ``_setup_cube_uri``), pinning the trailing-slash behavior
documented in issue #76.

These tests exercise the *real* ``Cube`` construction path offline. The
autouse fixture in ``tests/unit/conftest.py`` mocks ``query_lindas`` (default
return ``False``) and blocks real sockets, so building a ``Cube`` never touches
the network. We pass ``local=True`` so the remote existence check is skipped
entirely.

A ``Cube`` can be built with a minimal ``cube_yaml`` because ``__init__`` only
reads ``Base-URI`` / ``Identifier`` / ``Version`` / ``Namespace`` and pops
``dimensions``; the dataframe is not inspected during construction. Note that
``_setup_shape_dicts`` mutates ``cube_yaml`` (``pop("dimensions")``), so every
instantiation uses a freshly built dict.
"""

import pandas as pd
from hypothesis import given, settings
from hypothesis import strategies as st

from pylindas.pycube.cube import Cube

# ---------------------------------------------------------------------------
# Task 9.1 — Properties 1 & 2 (base-URI normalization + cube URI construction)
# ---------------------------------------------------------------------------

# A minimal, 1-row dataframe and single key dimension are enough for the
# construction path; the frame content is never read during __init__.
_MINIMAL_DATAFRAME = pd.DataFrame({"k": ["a"]})

# URL-safe characters for the random path segment / identifier / version. We
# deliberately avoid "/" and other reserved characters so that the join and
# equality contracts are about normalization, not URL-encoding edge cases.
_SAFE_ALPHABET = "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789-"

# Fixed scheme + host so every generated base URI is well-formed.
_FIXED_PREFIX = "https://example.org/"

safe_text = st.text(alphabet=_SAFE_ALPHABET, min_size=1, max_size=20)
# Versions are kept simple (small positive integers rendered as strings) so the
# constructed URI is clean and the equality contract is unambiguous.
version_text = st.integers(min_value=0, max_value=9999).map(str)


def _make_cube_yaml(base_uri: str, identifier: str, version: str) -> dict:
    """Build a fresh minimal ``cube_yaml`` for a single ``Cube`` construction."""
    return {
        "Base-URI": base_uri,
        "Identifier": identifier,
        "Version": version,
        "Namespace": "ns",
        "dimensions": {"k": {"dimension-type": "Key Dimension"}},
    }


def _build_cube(base_uri: str, identifier: str = "ident", version: str = "1") -> Cube:
    """Construct a ``Cube`` in local mode (no remote existence check)."""
    return Cube(
        dataframe=_MINIMAL_DATAFRAME,
        cube_yaml=_make_cube_yaml(base_uri, identifier, version),
        environment="TEST",
        local=True,
    )


# Feature: pylindas-modernization, Property 1: normalized base URI equals the base string with all trailing slashes stripped
@settings(max_examples=100)
@given(
    path=safe_text,
    trailing_slashes=st.integers(min_value=0, max_value=8),
    identifier=safe_text,
    version=version_text,
)
def test_base_uri_normalization_strips_all_trailing_slashes(
    path, trailing_slashes, identifier, version
):
    """Validates: Requirements 12.1, 12.2

    For a base URI with zero/one/many trailing "/" characters, the normalized
    base URI (``Cube._base_uri``) equals the input string with ALL trailing
    slashes removed, and ends in a non-slash character (the stripped string is
    always non-empty here because of the fixed scheme+host prefix).
    """
    base = _FIXED_PREFIX + path
    base_with_slashes = base + ("/" * trailing_slashes)

    cube = _build_cube(base_with_slashes, identifier=identifier, version=version)

    expected = base_with_slashes.rstrip("/")
    assert str(cube._base_uri) == expected
    # The stripped base is non-empty (fixed prefix guarantees content), so it
    # must end in a non-slash character.
    assert expected != ""
    assert not str(cube._base_uri).endswith("/")
    # When there were no trailing slashes, normalization is a no-op (Req 12.2).
    if trailing_slashes == 0:
        assert str(cube._base_uri) == base


# Feature: pylindas-modernization, Property 2: cube URI is base/identifier/version joined by single slashes and is invariant to trailing-slash count
@settings(max_examples=100)
@given(
    path=safe_text,
    identifier=safe_text,
    version=version_text,
    slashes_a=st.integers(min_value=0, max_value=8),
    slashes_b=st.integers(min_value=0, max_value=8),
)
def test_cube_uri_construction_and_trailing_slash_invariance(
    path, identifier, version, slashes_a, slashes_b
):
    """Validates: Requirements 12.3, 12.4

    The cube URI constructed in local mode equals
    ``URIRef(normalized_base + "/" + Identifier + "/" + Version)``; and for two
    Base-URIs differing only in the number of trailing slashes the constructed
    cube URIs are string-equal.
    """
    base = _FIXED_PREFIX + path
    normalized_base = base.rstrip("/")  # base has no trailing slash by design
    expected_cube_uri = f"{normalized_base}/{identifier}/{version}"

    base_a = base + ("/" * slashes_a)
    base_b = base + ("/" * slashes_b)

    cube_a = _build_cube(base_a, identifier=identifier, version=version)
    cube_b = _build_cube(base_b, identifier=identifier, version=version)

    # Req 12.3: base / identifier / version joined by single "/" separators.
    assert str(cube_a._cube_uri) == expected_cube_uri

    # Req 12.4: differing only in trailing-slash count yields equal cube URIs.
    assert str(cube_a._cube_uri) == str(cube_b._cube_uri)


# ---------------------------------------------------------------------------
# Task 9.2 — Properties 3 & 4 (local-mode no remote check + exists exception)
# ---------------------------------------------------------------------------
#
# These tests exercise the *real* ``Cube`` construction path offline, taking
# explicit control of the ``query_lindas`` entry point. ``cube.py`` binds
# ``query_lindas`` by value (``from pylindas.lindas.query import query_lindas``),
# so the name patched here is ``pylindas.pycube.cube.query_lindas``. Each test
# installs its own mock via ``unittest.mock.patch`` so it controls the
# call-count / return-value assertion for the duration (overriding the autouse
# fixture's shared mock).

from unittest.mock import patch

import pytest

from pylindas.lindas.exceptions import CubeAlreadyExistsError


# Feature: pylindas-modernization, Property 3: Local mode performs no remote existence check
@settings(max_examples=100)
@given(
    path=safe_text,
    identifier=safe_text,
    version=version_text,
)
def test_local_mode_performs_no_remote_existence_check(path, identifier, version):
    """Validates: Requirements 8.4, 12.5

    For any Base-URI / Identifier / Version, constructing a ``Cube`` with
    ``local=True`` performs NO remote cube-existence query (``query_lindas`` is
    never called) and never raises ``CubeAlreadyExistsError``.
    """
    base = _FIXED_PREFIX + path

    # Install our own mock so we can assert it is never consulted. Return True
    # so that *if* the local path ever reached the existence check, the resource
    # would appear to exist and the construction would raise — making an
    # accidental remote check a loud failure rather than a silent pass.
    with patch(
        "pylindas.pycube.cube.query_lindas", return_value=True
    ) as mock_query:
        cube = _build_cube(base, identifier=identifier, version=version)

        # No remote existence query was performed in local mode.
        mock_query.assert_not_called()

    # The cube was constructed successfully (no already-exists exception).
    expected_cube_uri = f"{base.rstrip('/')}/{identifier}/{version}"
    assert str(cube._cube_uri) == expected_cube_uri


# Feature: pylindas-modernization, Property 4: Non-local already-exists exception carries the constructed URI
@settings(max_examples=100)
@given(
    path=safe_text,
    identifier=safe_text,
    version=version_text,
)
def test_non_local_already_exists_exception_carries_uri(path, identifier, version):
    """Validates: Requirements 8.1, 8.2, 8.3

    For any Base-URI / Identifier / Version, when the remote existence check
    reports the resource EXISTS and ``local=False``, constructing the ``Cube``
    raises ``CubeAlreadyExistsError`` whose ``.uri`` / message carries the exact
    constructed cube URI, and which is NEVER a ``SystemExit``.
    """
    base = _FIXED_PREFIX + path
    normalized_base = base.rstrip("/")
    expected_cube_uri = f"{normalized_base}/{identifier}/{version}"

    # Simulate "resource exists" on the remote existence check.
    with patch("pylindas.pycube.cube.query_lindas", return_value=True):
        with pytest.raises(CubeAlreadyExistsError) as exc_info:
            Cube(
                dataframe=_MINIMAL_DATAFRAME,
                cube_yaml=_make_cube_yaml(base, identifier, version),
                environment="TEST",
                local=False,
            )

    error = exc_info.value
    # The exception carries the exact constructed URI, both as an attribute and
    # within the human-readable message.
    assert error.uri == expected_cube_uri
    assert expected_cube_uri in str(error)
    # It is a catchable, non-terminating exception — never a process exit.
    assert not isinstance(error, SystemExit)
