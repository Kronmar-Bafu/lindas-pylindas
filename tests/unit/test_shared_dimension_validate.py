"""Targeted example tests for two correctness fixes.

Design reference: Testing Strategy — Example/edge-case tests.

Concern A — GeoSharedDimension dead-code removal (Requirement 4.3):
    The dead ``_setup_graph()`` method (which referenced the non-existent
    ``self._cube_dict``) was removed from
    ``pylindas/pycube/shared_dimension.py`` and the stale ``py_cube`` import was
    corrected to ``pylindas.lindas.namespaces``. These tests prove the module
    imports cleanly and no longer exposes ``_setup_graph``.

Concern B — validate recursion fix (Requirements 5.1, 5.3, 5.4):
    ``pylindas/lindas/validate.py`` now aliases ``from pyshacl import validate
    as pyshacl_validate`` so the module-local ``validate`` no longer shadows and
    recursively calls itself. These tests mock ``pyshacl_validate`` to prove it
    is invoked exactly once (no recursion) and that ``validate`` returns the
    ``(conforms, text)`` 2-tuple shape.

These tests run under the ``tests/unit`` autouse ``_no_network`` fixture, so
they are fully offline; only ``pyshacl`` is mocked.
"""

import importlib
from unittest.mock import MagicMock, patch

from rdflib import Graph


# ---------------------------------------------------------------------------
# Concern A: GeoSharedDimension dead-code removal (Requirement 4.3)
# ---------------------------------------------------------------------------


def test_shared_dimension_module_imports_cleanly():
    """Importing the module must not raise (stale ``py_cube`` import fixed)."""
    module = importlib.import_module("pylindas.pycube.shared_dimension")
    assert module is not None


def test_geo_shared_dimension_has_no_setup_graph():
    """The dead ``_setup_graph`` method must be gone from the class."""
    from pylindas.pycube.shared_dimension import GeoSharedDimension

    assert not hasattr(GeoSharedDimension, "_setup_graph")


def test_shared_dimension_module_exposes_public_names():
    """Sanity: the module still exposes the public API it is supposed to."""
    module = importlib.import_module("pylindas.pycube.shared_dimension")

    assert hasattr(module, "convert_geojson_to_ttl")
    assert hasattr(module, "GeoSharedDimension")


# ---------------------------------------------------------------------------
# Concern B: validate recursion fix (Requirements 5.1, 5.3, 5.4)
# ---------------------------------------------------------------------------


def test_validate_imports_without_error():
    """Importing the validate module must not raise."""
    module = importlib.import_module("pylindas.lindas.validate")
    assert hasattr(module, "validate")


def test_validate_calls_pyshacl_exactly_once_and_returns_tuple():
    """``validate`` delegates to ``pyshacl_validate`` once and returns (conforms, text).

    The real ``pyshacl.validate`` returns a 3-tuple
    ``(conforms, results_graph, text)``; ``validate`` unpacks it and returns the
    ``(conforms, text)`` 2-tuple. Mocking the aliased symbol proves there is no
    self-recursion (exactly one call) and confirms the returned tuple shape.
    """
    from pylindas.lindas import validate as validate_module

    data_graph = Graph()
    shacl_graph = Graph()
    results_graph_sentinel = MagicMock(name="results_graph")

    mock_pyshacl = MagicMock(
        return_value=(True, results_graph_sentinel, "report text")
    )

    with patch.object(validate_module, "pyshacl_validate", mock_pyshacl):
        result = validate_module.validate(
            data_graph=data_graph, shacl_graph=shacl_graph
        )

    # Exactly one call proves no infinite recursion / no self-call (Req 5.1, 5.3).
    mock_pyshacl.assert_called_once()

    # Verify the call signature: data_graph positional, plus the expected kwargs.
    call = mock_pyshacl.call_args
    passed_args = call.args
    passed_kwargs = call.kwargs

    # data_graph is passed through (positional in validate.py).
    assert data_graph in passed_args or passed_kwargs.get("data_graph") is data_graph
    # shacl_graph is passed through as a kwarg.
    assert passed_kwargs.get("shacl_graph") is shacl_graph
    assert passed_kwargs.get("abort_on_first") is True
    assert passed_kwargs.get("inference") == "none"
    assert passed_kwargs.get("advanced") is True

    # The 2-tuple (conforms, text) shape is returned (Req 5.4).
    assert result == (True, "report text")


def test_validate_does_not_recurse():
    """A single-call mock guarantees no RecursionError is raised."""
    from pylindas.lindas import validate as validate_module

    mock_pyshacl = MagicMock(return_value=(False, MagicMock(), "nonconforming"))

    with patch.object(validate_module, "pyshacl_validate", mock_pyshacl):
        conforms, text = validate_module.validate(
            data_graph=Graph(), shacl_graph=Graph()
        )

    assert conforms is False
    assert text == "nonconforming"
    mock_pyshacl.assert_called_once()
