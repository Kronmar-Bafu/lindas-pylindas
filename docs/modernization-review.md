# Modernization Review

Review of `lindas-pylindas` captured on 2026-10-20 (branch `fix/issue-76`).
Starting point for a dedicated modernization session. All 25 existing tests
pass on Python 3.12.

## 1. Bugs and dead code (fix first)

### 1.1 `pylindas/cli.py` is broken — stale `py_cube` imports
The package was renamed `py_cube` → `pylindas`, but the CLI was never updated:

```python
import py_cube
from py_cube.fetch import fetch
from py_cube.example import list_examples, load_example
from py_cube.cube.shared_dimension import convert_geojson_to_ttl
```

Problems:
- `py_cube` no longer exists.
- Module path `cube.shared_dimension` is wrong; it is `pycube.shared_dimension`.
- `py_cube.Cube(...)` in `serialize()` must become `pylindas.Cube(...)`.

Impact: the `pycube` console entry point declared in `pyproject.toml`
(`pycube = "pylindas.cli:main"`) crashes on import. The CLI is unusable.

### 1.2 `pylindas/pycube/shared_dimension.py` — stale import + dead method
- `from py_cube.lindas.namespaces import *` → should be `pylindas.lindas.namespaces`.
- `_setup_graph()` references `self._cube_dict`, which does not exist on
  `GeoSharedDimension`. The method is never called (dead code). Either remove it
  or fix the attribute reference.

### 1.3 `pylindas/lindas/validate.py` — infinite recursion
```python
from pyshacl import validate
def validate(data_graph, shacl_graph):   # shadows the import
    conforms, ... = validate(...)         # calls itself -> stack overflow
```
Nothing imports this module today, so it is latent. Fix the shadowing (rename the
local function or alias the import) or delete the module.

### 1.4 `cli.py` schema subcommand is unreachable / mis-wired
- Parser registers `schema import`, but `main()` checks
  `args.suboperation == "import-description"`. The branch can never run.
- The `output` positional and `-v` are attached to the parent `schema_parser`
  rather than the `import` subparser, so the argument structure is inconsistent
  with the other subcommands.

## 2. Modernization opportunities

### 2.1 Packaging metadata (`pyproject.toml`)
- `requires-python = ">=3.10.11"` — unusual patch-level floor. Prefer `>=3.10`.
- `Homepage = "https://github.com/Kronmar-Bafu/py-cube"` — stale repo name.
- Dependencies are exact-pinned in `requirements.txt` and consumed dynamically.
  For a library this is restrictive for downstream users. Suggest moving runtime
  deps to `[project.dependencies]` with lower bounds (`>=`), and keeping exact
  pins in a separate dev/lock file (e.g. `requirements-dev.txt` or a lock).

### 2.2 Add tooling: linter / formatter / type checker
No `ruff`, `black`, or `mypy` today (only a `.prettierrc` for Markdown/JSON).
Adding `ruff` is the highest-leverage change: it would immediately flag the dead
imports above and unused imports in `cube.py` (`import numbers`, `import sys`
usage review). Wire it into CI.

### 2.3 Deprecation warnings
Test run produces ~611 deprecation warnings, mostly from `rdflib` / `pyparsing`
(`setParseAction`, `delimitedList`, `parseString`, `parseAll`). Bump `rdflib`
(currently pinned `7.0.0`) and re-review.

### 2.4 Library hygiene
- `Cube._setup_cube_uri` calls `sys.exit()` when a cube already exists; a library
  should raise an exception instead of killing the interpreter. Same pattern in
  `SharedDimension._setup_sd_dict`.
- `cube.py` uses `print()` for error/debug output while `cli.py` configures a
  proper `logging` logger. Standardize on `logging`.

## 3. Test coverage gaps (primary goal)

Existing tests (`tests/test_cube.py`, `test_sdterms.py`,
`test_shared_dimension_generation.py`) are all integration-level: they build full
cubes from example data and assert via SPARQL `ASK` queries. Valuable, but the
unit-level logic is untested.

High-value unit tests to add:
- `Cube._sanitize_value` — pure function; branches: NA → `cube:Undefined`, URI,
  lang-tagged, typed datatype, bare literal.
- Base-URI normalization / `_setup_cube_uri` — directly relevant to issue #76
  (current branch) but has no unit test pinning trailing-slash behavior.
- `Cube._replace_placeholders` — placeholder substitution.
- `Cube._get_accrual_periodicity` — mapping of each periodicity string.
- `Cube._construct_obs_uri` — URL-encoding of special characters in key dims.
- `fetch.py` `DataEuropaFetcher` inference helpers (`_infer_scale_type`,
  `_infer_dimension_type`, `_infer_temporal_dimension`) — pure functions.
- `cli.py` — once fixed, smoke-test argument parsing and `serialize`.

Other gaps:
- `tests/test_lindas.py` is an empty stub (single `pass`).
- `pylindas/lindas/upload.py` and `query.py` untested (need mocking of stardog /
  SPARQL endpoints).

## 4. Suggested order of work

1. Fix broken imports in `cli.py` and `pycube/shared_dimension.py`; fix or delete
   `lindas/validate.py` recursion. (Correctness first.)
2. Add `ruff` + config and wire into CI to catch this class of issue going forward.
3. Add a unit-test layer (pure functions in `cube.py`, Base-URI normalization,
   `fetch.py` inference, `_sanitize_value`).
4. Tidy packaging metadata and address deprecation warnings.
