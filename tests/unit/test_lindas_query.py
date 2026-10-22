"""Mock-based unit tests for ``pylindas/lindas/query.py``.

Design reference: Testing Strategy (Example/edge-case tests), Requirement 18.3
(query endpoint mocked, query operation invoked, boolean result propagated) and
Requirement 18.4 (no network requests during unit tests).

``query.py`` does ``from SPARQLWrapper import SPARQLWrapper``, which binds a
module-local name ``pylindas.lindas.query.SPARQLWrapper`` at import time. These
tests patch that local name so the real endpoint is never constructed and the
return values are fully controlled. The autouse ``_no_network`` fixture in
``conftest.py`` additionally guards against any accidental socket use.
"""

from unittest.mock import MagicMock, patch

import pytest

from pylindas.lindas import query as query_module
from pylindas.lindas.query import cube_exists, query_lindas


# Mapping of environment -> expected SPARQL endpoint URL used by query_lindas.
_ENV_ENDPOINTS = {
    "TEST": "https://test.lindas.admin.ch/query",
    "INT": "https://int.lindas.admin.ch/query",
    "PROD": "https://lindas.admin.ch/query",
}


def test_query_lindas_uses_sparqlwrapper_and_returns_boolean():
    """query_lindas wires up SPARQLWrapper and propagates the boolean result."""
    query = "ASK { ?s ?p ?o }"

    with patch("pylindas.lindas.query.SPARQLWrapper") as MockSW:
        inst = MockSW.return_value
        inst.query.return_value.convert.return_value = {"boolean": True}

        result = query_lindas(query, environment="TEST")

    # Constructed against the TEST endpoint URL.
    MockSW.assert_called_once_with("https://test.lindas.admin.ch/query")

    # Query and return format were configured (setQuery is called as a kwarg).
    inst.setQuery.assert_called_once_with(query=query)
    inst.setReturnFormat.assert_called_once()

    # The SPARQL query was executed and its result converted.
    inst.query.assert_called_once_with()
    inst.query.return_value.convert.assert_called_once_with()

    # The ["boolean"] value is returned.
    assert result is True


@pytest.mark.parametrize("environment,expected_url", list(_ENV_ENDPOINTS.items()))
def test_query_lindas_env_endpoints(environment, expected_url):
    """Each environment maps to its correct SPARQL endpoint URL."""
    with patch("pylindas.lindas.query.SPARQLWrapper") as MockSW:
        inst = MockSW.return_value
        inst.query.return_value.convert.return_value = {"boolean": False}

        result = query_lindas("ASK { ?s ?p ?o }", environment=environment)

    MockSW.assert_called_once_with(expected_url)
    assert result is False


def test_cube_exists_builds_ask_and_delegates():
    """cube_exists builds the ASK query and delegates to query_lindas."""
    cube_uri = "http://x/y"

    with patch.object(
        query_module, "query_lindas", MagicMock(return_value=True)
    ) as mock_query_lindas:
        result = cube_exists(cube_uri, "TEST")

    assert result is True

    # Delegated exactly once with the constructed ASK query and environment.
    mock_query_lindas.assert_called_once()
    args, kwargs = mock_query_lindas.call_args
    passed_query = args[0] if args else kwargs["query"]
    assert f"ASK {{ <{cube_uri}> ?p ?o}}" in passed_query
    assert kwargs["environment"] == "TEST"
