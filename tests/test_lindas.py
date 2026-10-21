"""Offline import / re-export sanity checks for the ``pylindas.lindas`` package.

This file lives in ``tests/`` (the integration-style suite), so it does NOT
receive the ``tests/unit/conftest.py`` autouse network isolation. Every test
here is therefore deliberately offline: we only import the public helpers and
make assertions about their identities and the exception hierarchy. We never
call ``query_lindas`` / ``upload_ttl`` / ``validate`` for real, since those
require network access or files.

Validates: Requirement 18.1
"""

import importlib

from pylindas.lindas.exceptions import (
    CubeAlreadyExistsError,
    ResourceExistsError,
    SharedDimensionAlreadyExistsError,
)
from pylindas.lindas.query import cube_exists, query_lindas
from pylindas.lindas.upload import upload_ttl
from pylindas.lindas.validate import validate


class TestLindasPackageImports:
    def test_package_imports_cleanly(self):
        module = importlib.import_module("pylindas.lindas")
        assert module is not None

    def test_public_helpers_are_callable(self):
        assert callable(query_lindas)
        assert callable(cube_exists)
        assert callable(upload_ttl)
        assert callable(validate)

    def test_exceptions_are_classes(self):
        assert isinstance(ResourceExistsError, type)
        assert isinstance(CubeAlreadyExistsError, type)
        assert isinstance(SharedDimensionAlreadyExistsError, type)


class TestExceptionHierarchy:
    def test_subclass_relationships(self):
        assert issubclass(CubeAlreadyExistsError, ResourceExistsError)
        assert issubclass(SharedDimensionAlreadyExistsError, ResourceExistsError)

    def test_cube_exists_error_carries_uri(self):
        uri = "http://example.org/cube/1"
        err = CubeAlreadyExistsError(uri)
        assert err.uri == uri
        assert uri in str(err)

    def test_exceptions_are_not_system_exit(self):
        # The whole point of the exception hierarchy is to replace sys.exit();
        # these must be ordinary catchable exceptions, never SystemExit.
        assert not issubclass(ResourceExistsError, SystemExit)
        assert not issubclass(CubeAlreadyExistsError, SystemExit)
        assert not issubclass(SharedDimensionAlreadyExistsError, SystemExit)

        err = CubeAlreadyExistsError("http://example.org/cube/1")
        assert not isinstance(err, SystemExit)
        assert isinstance(err, Exception)
