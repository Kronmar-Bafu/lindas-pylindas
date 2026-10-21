"""Property-based tests for ``Cube._sanitize_value``.

Design reference: Testing Strategy — Property-based tests (Requirement 11).

``Cube._sanitize_value(value, datatype, lang=None)`` dispatches a dataframe cell
value into an rdflib term. Its branch order is:

    if pd.isna(value):          -> Literal("", datatype=CUBE.Undefined)   # NA wins
    elif datatype == "URI":     -> URIRef(value)
    elif lang is not None:      -> Literal(value, lang=lang)
    elif datatype is not None:  -> Literal(value, datatype=getattr(XSD, datatype))
    else:                       -> Literal(value)

These tests exercise the branch dispatch (Property 5) and the NA precedence
guarantee (Property 6) against the real implementation — no reimplementation.
"""

import math

import pandas as pd
from hypothesis import given, settings
from hypothesis import strategies as st
from rdflib import Literal, URIRef, XSD

from pylindas.lindas.namespaces import CUBE
from pylindas.pycube.cube import Cube


# A small set of valid language tags and XSD datatype names to drive the
# language-tagged and typed-literal branches with realistic inputs.
LANG_TAGS = ["de", "fr", "en", "it"]
# ``string`` and ``gYear``/``date`` accept arbitrary lexical forms; we keep the
# set to datatypes that do not emit lexical-validation warnings for random text
# (the datatype branch only asserts the attached datatype, not lexical validity).
XSD_DATATYPES = ["string", "gYear", "date", "token", "normalizedString", "anyURI"]

# Non-NA scalar values. Text and integers-rendered-to-str are always non-NA and
# are the kinds of values the cube serializer hands to ``_sanitize_value``.
non_na_values = st.one_of(
    st.text(min_size=1, max_size=20),
    st.integers().map(str),
)


# Feature: pylindas-modernization, Property 5: Value sanitization branch dispatch
@settings(max_examples=200)
@given(
    value=non_na_values,
    datatype=st.sampled_from(XSD_DATATYPES),
    lang=st.sampled_from(LANG_TAGS),
    branch=st.sampled_from(["uri", "lang", "datatype", "plain"]),
)
def test_sanitize_value_branch_dispatch(value, datatype, lang, branch):
    """For a non-NA value, the correct branch fires based on datatype/lang."""
    # Guard: these generated values must never be considered NA, otherwise the
    # NA branch (tested separately) would pre-empt the branch under test.
    assert not pd.isna(value)

    if branch == "uri":
        result = Cube._sanitize_value(value, "URI", lang=None)
        assert isinstance(result, URIRef)
        assert str(result) == str(value)

    elif branch == "lang":
        # datatype is not "URI" and lang is non-null -> language-tagged Literal.
        result = Cube._sanitize_value(value, None, lang=lang)
        assert isinstance(result, Literal)
        assert result.language == lang
        assert str(result) == str(value)

    elif branch == "datatype":
        # Non-URI datatype, null lang -> typed Literal with the XSD datatype.
        result = Cube._sanitize_value(value, datatype, lang=None)
        assert isinstance(result, Literal)
        assert result.datatype == getattr(XSD, datatype)
        assert result.language is None

    else:  # branch == "plain"
        # Null datatype, null lang -> plain Literal, no datatype, no language.
        result = Cube._sanitize_value(value, None, lang=None)
        assert isinstance(result, Literal)
        assert result.language is None
        assert result.datatype is None
        assert str(result) == str(value)


# Feature: pylindas-modernization, Property 6: NA precedence in value sanitization
@settings(max_examples=200)
@given(
    na_value=st.sampled_from([float("nan"), None, pd.NA]),
    datatype=st.sampled_from([None, "URI", "string", "gYear", "date"]),
    lang=st.sampled_from([None, "de", "fr", "en", "it"]),
)
def test_sanitize_value_na_precedence(na_value, datatype, lang):
    """NA inputs always yield an empty cube:Undefined Literal, regardless of
    the datatype or language arguments (the NA branch pre-empts all others)."""
    # Precondition: the chosen value really is NA per pandas.
    assert pd.isna(na_value)

    result = Cube._sanitize_value(na_value, datatype, lang=lang)

    assert isinstance(result, Literal)
    assert result.datatype == CUBE.Undefined
    # Lexical (string) value is the empty string.
    assert str(result) == ""
    # Sanity: the NaN float never leaks through as the lexical value.
    assert not (isinstance(na_value, float) and math.isnan(na_value)) or str(result) == ""
