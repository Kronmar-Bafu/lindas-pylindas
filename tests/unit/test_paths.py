"""Unit tests for the path-safety validator.

Covers the path-traversal hardening applied to user-supplied CLI/download
paths (SonarCloud S8707).
"""

import pytest

from pylindas.lindas.paths import reject_traversal, UnsafePathError


def test_plain_filename_is_allowed(tmp_path):
    # A normal filename like "herbert.csv" is fine - no traversal.
    reject_traversal("herbert.csv", base_dir=str(tmp_path))


def test_nested_relative_path_allowed(tmp_path):
    reject_traversal("sub/dir/data.csv", base_dir=str(tmp_path))


def test_absolute_path_is_allowed(tmp_path):
    # Absolute paths are an explicit, trusted choice.
    reject_traversal(str(tmp_path / "out.ttl"))


def test_parent_traversal_is_rejected(tmp_path):
    with pytest.raises(UnsafePathError):
        reject_traversal("../escape.txt", base_dir=str(tmp_path))


def test_deep_parent_traversal_is_rejected(tmp_path):
    with pytest.raises(UnsafePathError):
        reject_traversal("sub/../../escape.txt", base_dir=str(tmp_path))


def test_empty_path_is_rejected():
    with pytest.raises(UnsafePathError):
        reject_traversal("")


def test_defaults_to_cwd(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    reject_traversal("data.csv")
    with pytest.raises(UnsafePathError):
        reject_traversal("../outside.csv")


def test_returns_none(tmp_path):
    # It is a pure validator: it must not return a usable (derived) path.
    assert reject_traversal("ok.csv", base_dir=str(tmp_path)) is None
