"""Mock-based unit tests for ``pylindas.lindas.upload.upload_ttl``.

Design reference: Testing Strategy — Network isolation (Requirements 18.2,
18.4). These tests exercise the *real* ``upload_ttl`` flow while mocking every
part that would otherwise touch a live Stardog endpoint or the filesystem:

* ``_load_config`` is patched so no ``lindas.ini`` file is required.
* ``stardog.Connection`` is patched so no real connection is opened; the
  context manager yields a ``MagicMock`` standing in for ``conn``.
* ``stardog.content.File`` is patched so building ``File(file=...)`` never
  touches disk.

The ``tests/unit`` autouse ``_no_network`` fixture additionally blocks real
sockets, so an accidental outbound connection becomes an immediate failure.
"""

from unittest.mock import MagicMock, patch

from pylindas.lindas import upload


def _make_conn_mock():
    """Return ``(mock_conn, mock_connection_cls)`` wired as a context manager.

    ``upload_ttl`` uses ``with stardog.Connection(...) as conn:``; the class is
    called, the returned object is entered, and ``__enter__`` yields ``conn``.
    """
    mock_conn = MagicMock(name="conn")
    conn_cm = MagicMock(name="connection_cm")
    conn_cm.__enter__.return_value = mock_conn
    conn_cm.__exit__.return_value = False
    mock_connection_cls = MagicMock(name="Connection", return_value=conn_cm)
    return mock_conn, mock_connection_cls


_DUMMY_CONFIG = {"endpoint": "x", "username": "u", "password": "p"}


def test_upload_ttl_single_file_begins_adds_commits():
    """A single-file upload begins, adds once, and commits — no clear."""
    mock_conn, mock_connection_cls = _make_conn_mock()

    with patch.object(upload, "_load_config", return_value=_DUMMY_CONFIG), patch(
        "stardog.Connection", mock_connection_cls
    ), patch("stardog.content.File", MagicMock(name="File")):
        upload.upload_ttl(
            filename="some.ttl",
            db_file="ignored.ini",
            environment="TEST",
            graph_uri="urn:graph",
            clear_graph=False,
        )

    mock_conn.begin.assert_called_once()
    mock_conn.add.assert_called_once()
    mock_conn.commit.assert_called_once()
    mock_conn.clear.assert_not_called()


def test_upload_ttl_clear_graph_calls_clear():
    """With ``clear_graph=True`` the graph is cleared before adding."""
    mock_conn, mock_connection_cls = _make_conn_mock()

    with patch.object(upload, "_load_config", return_value=_DUMMY_CONFIG), patch(
        "stardog.Connection", mock_connection_cls
    ), patch("stardog.content.File", MagicMock(name="File")):
        upload.upload_ttl(
            filename="some.ttl",
            db_file="ignored.ini",
            environment="TEST",
            graph_uri="urn:graph",
            clear_graph=True,
        )

    mock_conn.clear.assert_called_once_with(graph_uri="urn:graph")
    mock_conn.begin.assert_called_once()
    mock_conn.add.assert_called_once()
    mock_conn.commit.assert_called_once()


def test_upload_ttl_list_of_files_adds_each():
    """A list of files results in one ``add`` per file and a single commit."""
    mock_conn, mock_connection_cls = _make_conn_mock()

    with patch.object(upload, "_load_config", return_value=_DUMMY_CONFIG), patch(
        "stardog.Connection", mock_connection_cls
    ), patch("stardog.content.File", MagicMock(name="File")):
        upload.upload_ttl(
            filename=["a.ttl", "b.ttl"],
            db_file="ignored.ini",
            environment="TEST",
            graph_uri="urn:graph",
            clear_graph=False,
        )

    assert mock_conn.add.call_count == 2
    mock_conn.commit.assert_called_once()
    # The real connection class was replaced by our mock: no live connection.
    assert mock_connection_cls.call_count == 1
