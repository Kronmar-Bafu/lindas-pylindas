"""Mock-based unit tests for ``pylindas.lindas.upload.upload_ttl``.

Design reference: Testing Strategy — Network isolation (Requirements 18.2,
18.4). These tests exercise the *real* ``upload_ttl`` flow while mocking every
part that would otherwise touch a live GraphDB endpoint or the filesystem:

* ``_load_config`` is patched so no ``lindas.ini`` file is required.
* ``requests.post`` / ``requests.delete`` are patched so no HTTP request is
  sent; each returns a mock response whose ``raise_for_status`` is a no-op.
* ``builtins.open`` is patched so reading the Turtle files never touches disk.

LINDAS runs on GraphDB, which implements the SPARQL 1.1 Graph Store HTTP
Protocol: appending a graph is a ``POST`` with ``Content-Type: text/turtle``
and clearing a graph is a ``DELETE``.

The ``tests/unit`` autouse ``_no_network`` fixture additionally blocks real
sockets, so an accidental outbound connection becomes an immediate failure.
"""

from unittest.mock import MagicMock, mock_open, patch

from pylindas.lindas import upload


_DUMMY_CONFIG = {
    "endpoint": "https://example.test/rdf-graphs/service",
    "username": "u",
    "password": "p",
}


def _ok_response():
    """A mock HTTP response whose ``raise_for_status`` does nothing."""
    resp = MagicMock(name="response")
    resp.raise_for_status.return_value = None
    return resp


def test_upload_ttl_single_file_posts_once_no_delete():
    """A single-file upload POSTs the Turtle once and does not clear."""
    mock_post = MagicMock(name="post", return_value=_ok_response())
    mock_delete = MagicMock(name="delete", return_value=_ok_response())

    with patch.object(upload, "_load_config", return_value=_DUMMY_CONFIG), patch(
        "pylindas.lindas.upload.requests.post", mock_post
    ), patch("pylindas.lindas.upload.requests.delete", mock_delete), patch(
        "builtins.open", mock_open(read_data=b"<a> <b> <c> .")
    ):
        upload.upload_ttl(
            filename="some.ttl",
            db_file="ignored.ini",
            environment="TEST",
            graph_uri="urn:graph",
            clear_graph=False,
        )

    mock_post.assert_called_once()
    mock_delete.assert_not_called()

    # POST targets the configured endpoint, the right named graph, as text/turtle.
    args, kwargs = mock_post.call_args
    assert args[0] == _DUMMY_CONFIG["endpoint"]
    assert kwargs["params"] == {"graph": "urn:graph"}
    assert kwargs["headers"]["Content-Type"] == "text/turtle"
    assert kwargs["auth"] is not None


def test_upload_ttl_clear_graph_deletes_then_posts():
    """With ``clear_graph=True`` the named graph is DELETEd before the POST."""
    mock_post = MagicMock(name="post", return_value=_ok_response())
    mock_delete = MagicMock(name="delete", return_value=_ok_response())

    with patch.object(upload, "_load_config", return_value=_DUMMY_CONFIG), patch(
        "pylindas.lindas.upload.requests.post", mock_post
    ), patch("pylindas.lindas.upload.requests.delete", mock_delete), patch(
        "builtins.open", mock_open(read_data=b"<a> <b> <c> .")
    ):
        upload.upload_ttl(
            filename="some.ttl",
            db_file="ignored.ini",
            environment="TEST",
            graph_uri="urn:graph",
            clear_graph=True,
        )

    mock_delete.assert_called_once()
    _, del_kwargs = mock_delete.call_args
    assert del_kwargs["params"] == {"graph": "urn:graph"}
    mock_post.assert_called_once()


def test_upload_ttl_list_of_files_posts_each():
    """A list of files results in one POST per file and no clear."""
    mock_post = MagicMock(name="post", return_value=_ok_response())
    mock_delete = MagicMock(name="delete", return_value=_ok_response())

    with patch.object(upload, "_load_config", return_value=_DUMMY_CONFIG), patch(
        "pylindas.lindas.upload.requests.post", mock_post
    ), patch("pylindas.lindas.upload.requests.delete", mock_delete), patch(
        "builtins.open", mock_open(read_data=b"<a> <b> <c> .")
    ):
        upload.upload_ttl(
            filename=["a.ttl", "b.ttl"],
            db_file="ignored.ini",
            environment="TEST",
            graph_uri="urn:graph",
            clear_graph=False,
        )

    assert mock_post.call_count == 2
    mock_delete.assert_not_called()


def test_upload_ttl_missing_endpoint_raises():
    """A config without an ``endpoint`` is a clear error, not a silent no-op."""
    with patch.object(
        upload, "_load_config", return_value={"username": "u", "password": "p"}
    ):
        try:
            upload.upload_ttl(
                filename="some.ttl",
                db_file="ignored.ini",
                environment="TEST",
                graph_uri="urn:graph",
            )
        except Exception as exc:
            assert "endpoint" in str(exc)
        else:
            raise AssertionError("expected an exception for missing endpoint")
