"""Shared pytest fixtures enforcing offline, deterministic execution for the
``tests/unit`` package.

Design reference: Testing Strategy — Network isolation (Requirements 16.4, 18.4).

Every unit test runs with an autouse fixture that:

1. Replaces the real ``socket.socket`` with a guard that raises on any attempt
   to open a socket, so an accidental outbound connection becomes an
   immediate, clear failure instead of a flaky, slow network call.
2. Mocks the LINDAS network entry points so nothing reaches a live endpoint by
   default:
   * ``pylindas.lindas.query.query_lindas`` and the already-bound copies in the
     modules that do ``from pylindas.lindas.query import query_lindas``
     (``pylindas.pycube.cube`` and
     ``pylindas.pyshareddimension.shared_dimension``). The default mock returns
     ``False`` so existence checks behave as "resource does not exist".
   * ``SPARQLWrapper.SPARQLWrapper`` so ``query.py`` cannot open a connection
     even if called directly.
   * ``stardog.Connection`` so ``upload.py`` cannot connect (guarded by import
     availability).

Individual tests can override the ``query_lindas`` behavior (e.g. to simulate
"resource exists") with their own ``monkeypatch``/``unittest.mock`` setup;
``monkeypatch`` automatically restores everything after each test.
"""

import socket

import pytest
from unittest.mock import MagicMock


# Entry points that import ``query_lindas`` by value and therefore keep a
# module-local reference that must be patched independently of the source
# module. Each is patched with ``raising=False`` so the fixture never errors if
# a module was not imported in a given test.
_QUERY_LINDAS_TARGETS = (
    "pylindas.lindas.query.query_lindas",
    "pylindas.pycube.cube.query_lindas",
    "pylindas.pyshareddimension.shared_dimension.query_lindas",
)


class GuardedSocket:
    """Stand-in for ``socket.socket`` that refuses to be instantiated.

    Any real socket construction during a unit test raises immediately with a
    clear message, turning accidental network use into an obvious failure.
    """

    def __init__(self, *args, **kwargs):
        raise RuntimeError("Network access is disabled in unit tests")


@pytest.fixture(autouse=True)
def _no_network(monkeypatch):
    """Autouse fixture making the whole unit package run fully offline."""
    # 1. Block real sockets. Applied at test time (after imports), so libraries
    #    that create sockets at import time are unaffected.
    monkeypatch.setattr(socket, "socket", GuardedSocket)

    # 2. Mock the LINDAS query entry points (default: resource does not exist).
    #    A single shared mock keeps behavior consistent across the bound copies.
    query_mock = MagicMock(return_value=False)
    for target in _QUERY_LINDAS_TARGETS:
        monkeypatch.setattr(target, query_mock, raising=False)

    # 3. Mock SPARQLWrapper so query.py cannot open a connection.
    try:
        import SPARQLWrapper as _sparql_wrapper

        monkeypatch.setattr(
            _sparql_wrapper, "SPARQLWrapper", MagicMock(), raising=False
        )
    except ImportError:
        pass

    # 4. Mock stardog.Connection so upload.py cannot connect (if importable).
    try:
        import stardog as _stardog

        monkeypatch.setattr(_stardog, "Connection", MagicMock(), raising=False)
    except ImportError:
        pass

    yield
