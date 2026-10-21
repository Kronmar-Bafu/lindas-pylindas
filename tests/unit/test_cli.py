"""Unit tests for the repaired :mod:`pylindas.cli` command-line interface.

This module pins the behavior of the CLI fixes made earlier in the
modernization effort:

* the module imports with no ``py_cube`` references (Requirements 2.1-2.5);
* ``serialize`` argument parsing forwards the input directory and output TTL
  path to the ``serialize`` handler (Requirement 17.1, 2.x);
* ``schema import`` dispatches to the import branch, writes the schema file,
  and exits zero, with ``output``/``-v`` living on the ``import`` subparser
  (Requirements 3.1-3.4);
* a missing required ``output`` produces an argparse usage error / non-zero
  exit (Requirement 3.5);
* invoking the CLI with a valid operation runs without an import-related
  failure and returns normally (Requirements 2.6, 2.7).

``main()`` builds its argparse parser inline and immediately parses
``sys.argv`` and dispatches, so these tests drive it the way a shell would:
``sys.argv`` is patched to the desired invocation and the downstream handler
functions (``serialize``, ``fetch``, ``load_example``,
``convert_geojson_to_ttl``) are patched so no real work or network happens.
The ``schema import`` branch performs real, local file I/O into pytest's
``tmp_path`` only. The ``tests/unit`` autouse fixture (``conftest.py``) blocks
real sockets, so any accidental network use fails loudly.

Design reference: CLI fixes (Component 1); Testing Strategy.

NOTE: Task 10.3 appends a serialize smoke test to this same file in a later
batch. These argument-parsing tests intentionally avoid any module-level
teardown so there is nothing for 10.3 to duplicate.
"""

import os

import pytest


# ---------------------------------------------------------------------------
# Section: CLI argument-parsing and schema-dispatch tests (Task 10.2)
# ---------------------------------------------------------------------------


def test_cli_imports_without_py_cube():
    """``pylindas.cli`` imports cleanly with no ``py_cube`` references.

    Confirms the import-correction table was applied: the module imports
    without error, exposes no ``py_cube`` module-level name, binds the
    ``pylindas`` ``Cube``, and successfully imported each handler dependency.

    Validates: Requirements 2.1, 2.2, 2.3, 2.4, 2.5
    """
    import pylindas.cli as cli
    from pylindas import Cube

    # No leftover ``py_cube`` module-level reference.
    assert not hasattr(cli, "py_cube")

    # ``Cube`` must be the pylindas Cube, not a py_cube alias.
    assert cli.Cube is Cube

    # Each CLI handler dependency imported successfully and is bound/callable.
    assert callable(cli.fetch)
    assert callable(cli.list_examples)
    assert callable(cli.load_example)
    assert callable(cli.convert_geojson_to_ttl)

    # The source file itself must not contain the ``py_cube`` token.
    source_path = cli.__file__
    with open(source_path, "r") as handle:
        source = handle.read()
    assert "py_cube" not in source


def test_serialize_argparsing(monkeypatch):
    """``serialize`` parsing forwards the input dir and output TTL path.

    The ``serialize`` handler is replaced with a mock so no cube is built; the
    assertion checks that ``main()`` parsed ``sys.argv`` and forwarded the
    positional arguments in the order ``main()`` dispatches them:
    ``serialize(input_directory, output_ttl, na_value, sep, decimal)``.

    Validates: Requirements 17.1, 2.1, 2.5
    """
    import pylindas.cli as cli
    from unittest.mock import MagicMock

    serialize_mock = MagicMock()
    monkeypatch.setattr(cli, "serialize", serialize_mock)
    monkeypatch.setattr("sys.argv", ["pycube", "serialize", "somedir", "out.ttl"])

    cli.main()

    serialize_mock.assert_called_once()
    args, kwargs = serialize_mock.call_args
    # main() dispatches positionally: input_directory, output_ttl, na, sep, dec.
    assert args[0] == "somedir"
    assert args[1] == "out.ttl"
    # Defaults for the optional CSV-parsing arguments are forwarded.
    assert args[3] == ","
    assert args[4] == "."


def test_schema_import_dispatch_and_args(tmp_path, monkeypatch):
    """``schema import`` writes the schema file and exits zero.

    Points ``output`` at a tmp file so the branch performs real local file
    I/O without touching the repo, then asserts the written contents match
    ``pylindas/description.schema.json`` exactly. Also confirms ``output`` and
    ``-v`` live on the ``import`` subparser: ``schema import x.json -v`` parses
    and dispatches cleanly.

    Validates: Requirements 3.1, 3.2, 3.3, 3.4
    """
    import pylindas.cli as cli

    output_file = tmp_path / "out.json"
    monkeypatch.setattr(
        "sys.argv", ["pycube", "schema", "import", str(output_file)]
    )

    # main() returns normally (implicit exit 0) on a successful import.
    result = cli.main()
    assert result is None

    # The output file was created with the schema file's exact contents.
    assert output_file.exists()
    schema_path = os.path.join(os.path.dirname(cli.__file__), "description.schema.json")
    with open(schema_path, "r") as handle:
        expected = handle.read()
    assert output_file.read_text() == expected

    # ``output`` and ``-v`` are on the ``import`` subparser: this parses and
    # dispatches without error (the ``-v`` is consumed by the subparser).
    verbose_output = tmp_path / "verbose.json"
    monkeypatch.setattr(
        "sys.argv",
        ["pycube", "schema", "import", str(verbose_output), "-v"],
    )
    cli.main()
    assert verbose_output.exists()


def test_schema_import_verbose_not_on_parent_parser(tmp_path, monkeypatch):
    """``-v`` belongs to the ``import`` subparser, not the parent ``schema``.

    Placing ``-v`` before the ``import`` subcommand (i.e. on the parent
    ``schema`` parser, which defines no such option) is a usage error and
    must terminate with a non-zero exit. This complements
    ``test_schema_import_dispatch_and_args`` by proving the option lives on
    the subparser rather than the parent.

    Validates: Requirements 3.2, 3.3
    """
    import pylindas.cli as cli

    monkeypatch.setattr(
        "sys.argv",
        ["pycube", "schema", "-v", str(tmp_path / "x.json")],
    )

    with pytest.raises(SystemExit) as exc_info:
        cli.main()

    assert exc_info.value.code != 0


def test_schema_import_missing_output_errors(monkeypatch):
    """``schema import`` without an output path is a usage error.

    argparse raises ``SystemExit(2)`` when the required ``output`` positional
    is absent.

    Validates: Requirements 3.5
    """
    import pylindas.cli as cli

    monkeypatch.setattr("sys.argv", ["pycube", "schema", "import"])

    with pytest.raises(SystemExit) as exc_info:
        cli.main()

    assert exc_info.value.code != 0


def test_cli_valid_operation_runs_without_import_failure(monkeypatch):
    """A valid operation runs without an import-related failure, exit zero.

    Requirements 2.6/2.7 concern the invocation-time exit status: a valid
    operation must complete without an import-related exception and return a
    zero exit status. Because the CLI dependencies are imported at module load
    (which already succeeded for this test to run), this asserts the positive
    path: dispatching a valid ``fetch`` operation returns normally (no
    ``SystemExit``, no ``ImportError``) with the handler mocked offline.

    The failure path of Requirement 2.7 (a dependency failing to import) cannot
    be simulated without altering Python's import machinery after the module
    has already loaded, so it is covered by the import-success assertions in
    ``test_cli_imports_without_py_cube`` rather than re-exercised here.

    Validates: Requirements 2.6, 2.7
    """
    import pylindas.cli as cli
    from unittest.mock import MagicMock

    fetch_mock = MagicMock()
    monkeypatch.setattr(cli, "fetch", fetch_mock)
    monkeypatch.setattr(
        "sys.argv", ["pycube", "fetch", "https://example.org/dataset", "outdir"]
    )

    # No ImportError, no SystemExit -> implicit zero exit status.
    result = cli.main()
    assert result is None
    fetch_mock.assert_called_once_with("https://example.org/dataset", "outdir")


# ---------------------------------------------------------------------------
# Task 10.3 — serialize smoke test
# ---------------------------------------------------------------------------
#
# This section exercises the repaired CLI ``serialize`` handler end-to-end
# against the local ``example/Cubes/mock`` cube and pins its TTL output against
# the committed reference. It runs fully offline: the cube is built with
# ``local=True`` (no existence check, no network) and the ``tests/unit``
# autouse fixture blocks real sockets.
#
# The output is compared to ``example/Cubes/mock/cube.ttl`` by *graph
# isomorphism* rather than text equality, and the two auto-generated timestamp
# triples (``schema:datePublished`` and ``schema:dateModified``) are removed
# from both graphs before the comparison so a run on a different day still
# matches. ``schema:dateCreated`` is stable (it comes from ``description.yml``)
# and is intentionally kept in the comparison.

from pathlib import Path

import rdflib
from rdflib import Namespace
from rdflib.compare import isomorphic, graph_diff


_SCHEMA = Namespace("http://schema.org/")

# Predicates whose objects are generated at serialization time and therefore
# vary run-to-run. These are stripped from both graphs before comparison.
_TIMESTAMP_PREDICATES = (_SCHEMA.datePublished, _SCHEMA.dateModified)

_MOCK_CUBE_DIR = "example/Cubes/mock"
_MOCK_REFERENCE_TTL = "example/Cubes/mock/cube.ttl"


def _strip_timestamp_triples(graph: rdflib.Graph) -> rdflib.Graph:
    """Return ``graph`` with all auto-generated timestamp triples removed.

    Removes every triple whose predicate is ``schema:datePublished`` or
    ``schema:dateModified`` (Requirement 17.3 — compare "excluding
    auto-generated timestamp triples"). ``schema:dateCreated`` is left intact
    because it is sourced from the cube description and is stable.
    """
    for predicate in _TIMESTAMP_PREDICATES:
        for subject, obj in list(graph.subject_objects(predicate)):
            graph.remove((subject, predicate, obj))
    return graph


def test_serialize_smoke_produces_isomorphic_ttl(tmp_path):
    """CLI ``serialize`` produces valid TTL isomorphic to the reference.

    Runs the repaired ``pylindas.cli.serialize`` handler against the local
    ``example/Cubes/mock`` cube, writing to a pytest ``tmp_path`` file (an
    absolute path, so the handler's ``os.path.join(os.getcwd(), output_ttl)``
    resolves to exactly that path — ``os.path.join`` discards the first
    component when the second is absolute). Nothing is written into the repo
    and ``tmp_path`` is auto-cleaned after the test (Requirement 17.4).

    Asserts the produced TTL exists, is non-empty, and parses as valid Turtle
    (Requirement 17.2), then asserts it is graph-isomorphic to the committed
    ``example/Cubes/mock/cube.ttl`` once the auto-generated timestamp triples
    are removed from both graphs (Requirement 17.3).

    Validates: Requirements 17.2, 17.3, 17.4
    """
    import pylindas.cli as cli

    output_ttl = tmp_path / "mock_cube.ttl"
    assert output_ttl.is_absolute()

    # Build + serialize the local example cube through the CLI handler. The
    # mock dir ships a description.yml and data.csv; local=True skips any
    # network existence check. na_values=None is a valid pandas read_csv value.
    cli.serialize(
        input_directory=_MOCK_CUBE_DIR,
        output_ttl=str(output_ttl),
        na_values=None,
    )

    # Requirement 17.2: a non-empty, parseable TTL file is produced.
    assert output_ttl.exists(), "serialize did not write the output TTL"
    assert output_ttl.stat().st_size > 0, "serialize produced an empty TTL file"

    produced = rdflib.Graph()
    produced.parse(output_ttl.as_posix(), format="turtle")
    assert len(produced) > 0, "parsed TTL contained no triples"

    # Requirement 17.3: graph-isomorphic to the committed reference, excluding
    # the auto-generated timestamp triples.
    reference = rdflib.Graph()
    reference.parse(Path(_MOCK_REFERENCE_TTL).as_posix(), format="turtle")

    _strip_timestamp_triples(produced)
    _strip_timestamp_triples(reference)

    if not isomorphic(produced, reference):
        # Surface the differing triples to aid diagnosis rather than failing
        # with an opaque boolean.
        _, in_reference_only, in_produced_only = graph_diff(reference, produced)
        only_ref = "\n".join(sorted(str(t) for t in in_reference_only))
        only_prod = "\n".join(sorted(str(t) for t in in_produced_only))
        pytest.fail(
            "Serialized TTL is not isomorphic to the committed reference "
            "after removing timestamp triples.\n"
            f"Only in reference:\n{only_ref}\n\n"
            f"Only in produced:\n{only_prod}"
        )


def test_serialize_smoke_keeps_date_created_in_comparison():
    """``schema:dateCreated`` is treated as stable, not a timestamp triple.

    Guards the stripping helper: ``dateCreated`` (sourced from
    ``description.yml``) must be preserved, while ``datePublished`` and
    ``dateModified`` (generated at serialize time) must be removed. This keeps
    the isomorphism check from silently ignoring a real, stable triple.

    Validates: Requirements 17.3
    """
    graph = rdflib.Graph()
    subject = rdflib.URIRef("https://example.org/cube")
    graph.add((subject, _SCHEMA.dateCreated, rdflib.Literal("2024-08-26")))
    graph.add((subject, _SCHEMA.datePublished, rdflib.Literal("2026-10-21")))
    graph.add((subject, _SCHEMA.dateModified, rdflib.Literal("2026-10-21")))

    _strip_timestamp_triples(graph)

    assert (subject, _SCHEMA.dateCreated, None) in graph
    assert (subject, _SCHEMA.datePublished, None) not in graph
    assert (subject, _SCHEMA.dateModified, None) not in graph
