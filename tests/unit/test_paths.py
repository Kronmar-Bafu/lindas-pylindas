"""Unit tests for the path-safety helper.

Covers the path-traversal hardening applied to user-supplied CLI/download
paths (SonarCloud S8707).
"""

import os

import pytest

from pylindas.lindas.paths import safe_path, UnsafePathError


def test_relative_path_resolves_within_base(tmp_path):
    result = safe_path("data.csv", base_dir=str(tmp_path))
    assert result == os.path.join(os.path.realpath(str(tmp_path)), "data.csv")


def test_nested_relative_path_allowed(tmp_path):
    result = safe_path("sub/dir/data.csv", base_dir=str(tmp_path))
    assert result.startswith(os.path.realpath(str(tmp_path)) + os.sep)
    assert result.endswith(os.path.join("sub", "dir", "data.csv"))


def test_absolute_path_is_honored(tmp_path):
    target = str(tmp_path / "out.ttl")
    # Absolute paths are an explicit, trusted choice and pass through normalized.
    assert safe_path(target) == os.path.normpath(target)


def test_parent_traversal_is_rejected(tmp_path):
    with pytest.raises(UnsafePathError):
        safe_path("../escape.txt", base_dir=str(tmp_path))


def test_deep_parent_traversal_is_rejected(tmp_path):
    with pytest.raises(UnsafePathError):
        safe_path("sub/../../escape.txt", base_dir=str(tmp_path))


def test_empty_path_is_rejected():
    with pytest.raises(UnsafePathError):
        safe_path("")


def test_defaults_to_cwd(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    result = safe_path("data.csv")
    assert result == os.path.join(os.path.realpath(str(tmp_path)), "data.csv")
