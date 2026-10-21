"""Property-based tests for ``Cube._replace_placeholders``.

Design reference: Property 7 (Placeholder substitution preserves absent
placeholders). Validates Requirements 13.1, 13.2, 13.3.

``_replace_placeholders`` is an instance method that does not use ``self``, so
it is exercised on a bare instance created with ``Cube.__new__(Cube)`` to avoid
constructing a full cube (which would need network/graph setup). The ``row``
argument only needs to support ``name in row`` and ``row[name]``, so a plain
dict is used — this matches how pandas rows behave for the membership/lookup
the method relies on, and keeps the test fully offline.
"""

from hypothesis import given, settings
from hypothesis import strategies as st

from pylindas.pycube.cube import Cube


# A "safe" alphabet for placeholder names: identifier-like, non-empty, and
# brace-free so the regex ``\{(.*?)\}`` sees unambiguous, well-delimited tokens.
_name_strategy = st.text(
    alphabet="abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789_",
    min_size=1,
    max_size=12,
)

# Values are kept brace-free so that str(value) can never introduce a new
# ``{...}`` token nor accidentally match an ``{absent}`` literal, keeping the
# assertions clean. Literal glue text is likewise brace-free so the only
# ``{...}`` tokens in a template come from the placeholders we inject.
_value_strategy = st.one_of(
    st.integers(),
    st.text(
        alphabet="abcdefghijklmnopqrstuvwxyz ABC0123456789-/:.",
        max_size=20,
    ),
)

_glue_strategy = st.text(
    alphabet="abcdefghijklmnopqrstuvwxyz ABC0123456789-/:.",
    max_size=10,
)


@st.composite
def _row_template(draw):
    """Build a (row, template, present_names, absent_names) tuple.

    ``present_names`` and ``absent_names`` are disjoint sets of identifier-like
    names; ``row`` maps each present name to a brace-free value. The template
    interleaves brace-free literal glue with ``{present}`` and ``{absent}``
    placeholder tokens in a random order.
    """
    present_names = draw(st.lists(_name_strategy, min_size=0, max_size=5, unique=True))
    absent_names = draw(
        st.lists(_name_strategy, min_size=0, max_size=5, unique=True).filter(
            lambda names: not (set(names) & set(present_names))
        )
    )

    row = {name: draw(_value_strategy) for name in present_names}

    # Interleave placeholder tokens with literal glue. Order of tokens is
    # randomized so present/absent placeholders can appear anywhere.
    tokens = [f"{{{name}}}" for name in present_names + absent_names]
    tokens = draw(st.permutations(tokens))

    parts = [draw(_glue_strategy)]
    for token in tokens:
        parts.append(token)
        parts.append(draw(_glue_strategy))
    template = "".join(parts)

    return row, template, present_names, absent_names


# Feature: pylindas-modernization, Property 7: Placeholder substitution preserves absent placeholders
@settings(max_examples=200)
@given(_row_template())
def test_placeholder_substitution_preserves_absent_placeholders(data):
    row, template, present_names, absent_names = data

    cube = Cube.__new__(Cube)
    result = cube._replace_placeholders(row, template)

    # Every present placeholder is replaced by the string form of its value,
    # and its raw ``{name}`` token no longer remains in the output.
    for name in present_names:
        expected_value = str(row[name])
        assert expected_value in result, (
            f"expected substituted value {expected_value!r} for present "
            f"placeholder {name!r} to appear in {result!r}"
        )
        assert f"{{{name}}}" not in result, (
            f"raw token {{{name}}} should have been replaced in {result!r}"
        )

    # Every absent placeholder's literal ``{name}`` token is left unchanged.
    for name in absent_names:
        assert f"{{{name}}}" in result, (
            f"absent placeholder token {{{name}}} should remain intact in "
            f"{result!r}"
        )
