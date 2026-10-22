"""Smoke tests for :mod:`pylindas.fetch`.

These tests confirm the fetch module and its public surface load and dispatch
correctly without touching the network. The ``tests/unit`` autouse fixture
(``conftest.py``) installs a socket guard that raises on any real connection
attempt, so any accidental network use fails loudly rather than reaching a live
``data.europa.eu`` endpoint.

Design reference: Testing Strategy — Network isolation (Requirements 16.1-16.4).
"""

from unittest.mock import MagicMock, patch


def test_fetch_module_imports():
    """``pylindas.fetch`` imports cleanly and exposes its public surface.

    Validates: Requirements 16.1
    """
    import pylindas.fetch  # noqa: F401 - import must not raise

    # The public names relied on by callers/tests must be importable.
    from pylindas.fetch import fetch, DataEuropaFetcher

    assert callable(fetch)
    assert isinstance(DataEuropaFetcher, type)


def test_data_europa_fetcher_instantiable_offline():
    """``DataEuropaFetcher()`` constructs without any network access.

    The autouse socket guard in ``conftest.py`` would raise if construction
    attempted to open a connection.

    Validates: Requirements 16.2
    """
    from pylindas.fetch import DataEuropaFetcher

    fetcher = DataEuropaFetcher()

    assert isinstance(fetcher, DataEuropaFetcher)


def test_fetch_dispatches_to_data_europa_fetcher(tmp_path):
    """``fetch()`` routes ``data.europa.eu`` URLs to ``DataEuropaFetcher``.

    The real ``fetch_dataset`` would make live HTTP requests, so the
    ``DataEuropaFetcher`` class is patched with a mock. This keeps the test
    offline while still exercising the real dispatch logic in ``fetch()``.
    ``output_dir`` points at pytest's ``tmp_path`` because ``fetch()`` creates
    the directory on disk before dispatching.

    Validates: Requirements 16.3, 16.4
    """
    import pylindas.fetch as fetch_module

    url = "https://data.europa.eu/data/datasets/some-id"
    output_dir = str(tmp_path / "out")

    with patch.object(fetch_module, "DataEuropaFetcher") as MockFetcher:
        instance = MagicMock()
        MockFetcher.return_value = instance

        fetch_module.fetch(url, output_dir)

    # The dispatcher must construct a DataEuropaFetcher ...
    MockFetcher.assert_called_once_with()
    # ... and delegate to fetch_dataset with the url and output dir.
    instance.fetch_dataset.assert_called_once_with(url, output_dir)
