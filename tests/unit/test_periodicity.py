"""Unit tests for ``Cube._get_accrual_periodicity``.

Covers Requirement 14 (accrual periodicity mapping). This file is populated in
two independent sections so they can be authored separately without conflict:

* Property-based test (Task 9.5 / Property 8): fall-through behavior for
  unsupported periodicity strings.
* Exhaustive parametrized mapping test (Task 10.1): the five supported
  periodicity strings map to their exact authority URI tokens.

The supported periodicity values recognized by ``_get_accrual_periodicity``.
Shared by both sections.
"""

from pylindas.pycube.cube import Cube

KNOWN_PERIODICITIES = {"daily", "weekly", "monthly", "yearly", "irregular"}


# ---------------------------------------------------------------------------
# Task 9.5 — Property-based test (Hypothesis)
# ---------------------------------------------------------------------------

from hypothesis import assume, given, settings
from hypothesis import strategies as st


# Feature: pylindas-modernization, Property 8: Accrual periodicity fall-through
@settings(max_examples=200)
@given(periodicity=st.text())
def test_property_accrual_periodicity_fall_through(periodicity):
    """Validates: Requirements 14.3

    For any string that is NOT one of the five supported periodicities,
    ``_get_accrual_periodicity`` returns ``None`` (the documented fall-through):
    no URIRef is produced for unrecognized input.
    """
    assume(periodicity not in KNOWN_PERIODICITIES)

    result = Cube._get_accrual_periodicity(periodicity)

    assert result is None


# ---------------------------------------------------------------------------
# Task 10.1 — Exhaustive parametrized mapping test
# ---------------------------------------------------------------------------

import pytest
from rdflib import URIRef

FREQUENCY_AUTHORITY_BASE = "http://publications.europe.eu/resource/authority/frequency/"


@pytest.mark.parametrize(
    ("periodicity", "token"),
    [
        ("daily", "DAILY"),
        ("weekly", "WEEKLY"),
        ("monthly", "MONTHLY"),
        ("yearly", "ANNUAL"),
        ("irregular", "IRREG"),
    ],
)
def test_accrual_periodicity_maps_to_authority_uri(periodicity, token):
    """Validates: Requirements 14.1

    Each of the five supported periodicity strings maps to the exact EU
    authority frequency URI (base + token), returned as an ``rdflib.URIRef``.
    """
    # The parametrization exhaustively covers every known periodicity.
    assert periodicity in KNOWN_PERIODICITIES

    expected = URIRef(FREQUENCY_AUTHORITY_BASE + token)

    result = Cube._get_accrual_periodicity(periodicity)

    assert isinstance(result, URIRef)
    assert result == expected
    assert str(result) == FREQUENCY_AUTHORITY_BASE + token


def test_yearly_maps_to_annual():
    """Validates: Requirements 14.2

    The "yearly" periodicity maps to the ``ANNUAL`` authority token (not a
    literal "YEARLY"); the resulting URI ends with ``ANNUAL``.
    """
    result = Cube._get_accrual_periodicity("yearly")

    assert isinstance(result, URIRef)
    assert str(result).endswith("ANNUAL")
    assert result == URIRef(FREQUENCY_AUTHORITY_BASE + "ANNUAL")
