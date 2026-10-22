# Code Duplication Findings

Read-only analysis of the `pylindas` package captured during the
`pylindas-modernization` spec work. These findings are **out of scope** for the
modernization spec (which is constrained to behavior-preserving changes) and are
recorded here as the starting point for a future, dedicated deduplication spec.

Deduplication must be its own effort because several copies have already
**diverged**, so merging them risks changing cube.link TTL output. A refactor
spec should gate every consolidation behind `rdflib.compare.isomorphic` over all
example cubes.

## Prioritized summary

| # | Cluster | Severity | Why it matters |
|---|---------|----------|----------------|
| 1 | `_sanitize_value()` copied verbatim (cube.py ↔ pyshareddimension) | High | Exact logic clone; diverges only in signature default. Bug fixes must be applied twice. |
| 2 | `_apply_mappings` / `_replace_placeholders` copied from cube.py into SharedDimension | High | Already divergent (cube.py has `concept`+`function` cases and `value-type` casting; SD version does not). Silent behavior drift. |
| 3 | SPARQL `ASK { <uri> ?p ?o }` + `query_lindas` + `sys.exit` existence check | High | Implemented 3×. The reusable helper `cube_exists()` already exists but is never used. |
| 4 | `query_lindas` reimplemented with a different return contract | High | Two functions, same name: one returns `["boolean"]`, the other full JSON. Easy to import the wrong one. |
| 5 | Environment → endpoint URL switch (TEST/INT/PROD) | Medium | Duplicated 4× with divergent defaults (query.py has no default and can `UnboundLocalError`). |
| 6 | `_setup_graph()` namespace-binding loop | Medium | 3 copies. The GeoSD copy is dead + buggy (references nonexistent `self._cube_dict`). |
| 7 | `serialize()` one-liner + copy-pasted docstring ("Serialize the cube") | Low–Medium | 3 identical bodies; docstring copy-paste tell in both SD modules. |
| 8 | URI construction `base + "/" + identifier` / `URIRef` / `rstrip("/")` | Low–Medium | Scattered; only cube.py normalizes trailing slash (issue #76). |

A shared `pylindas/lindas/graph_utils.py` (graph setup, serialize, URI helpers,
`sanitize_value`) plus consolidating all SPARQL/endpoint logic into
`pylindas/lindas/query.py` would eliminate clusters 1, 3, 5, 6, 7, 8.

## Cluster 1 — `_sanitize_value()` verbatim clone (High)

Identical static method, body byte-for-byte the same.

- `pylindas/pycube/cube.py:925-947` — `Cube._sanitize_value(value, datatype, lang=None)`
- `pylindas/pyshareddimension/shared_dimension.py:405-427` — `SharedDimension._sanitize_value(value, datatype, lang)`

Divergence: only the signature (cube.py defaults `lang=None`; SD requires `lang`
positionally). Bodies identical.
Suggested home: `graph_utils.sanitize_value(value, datatype, lang=None)`.

## Cluster 2 — mapping engine copied into SharedDimension (High)

- `pylindas/pycube/cube.py:271` — `Cube._apply_mappings` (cases: additive, replace, regex, concept, function; plus `value-type` Shared/Literal casting)
- `pylindas/pyshareddimension/shared_dimension.py:239-268` — `SharedDimension._apply_mappings` (comment at line 240: "Adapted directly from the _apply_mappings in cube.py")
- `_replace_placeholders` duplicated: `cube.py` and `shared_dimension.py:270-275`

Near-identical but **divergent**: SD's `additive` uses `base + df.astype(str)`
while cube uses URL-quoting (SD loses quoting); SD lacks the `function` case and
the `value-type` casting; `concept` base differs. Divergence hides bugs.
Suggested home: a shared mapping helper taking `(dataframe, mapping_dict, base_uri)`.

## Cluster 3 — SPARQL ASK existence check + `sys.exit` (High)

- `pylindas/pycube/cube.py:203-207` — in `_setup_cube_uri`
- `pylindas/pyshareddimension/shared_dimension.py:147-150` — in `_setup_sd_dict`
- `pylindas/lindas/query.py:17-28` — `cube_exists()` encapsulates exactly this query but is **never called**.

Note: the modernization spec (Requirement 8) replaces the two `sys.exit` calls
with exceptions. A later refactor should also route both callers through
`cube_exists()`.
Suggested home: reuse `lindas.query.cube_exists(...)`.

## Cluster 4 + 5 — `query_lindas` duplicate + endpoint switch (High / Medium)

Two functions named `query_lindas` with different return contracts:

- `pylindas/lindas/query.py:3-14` — returns `results["boolean"]` (no default case → missing env raises `UnboundLocalError`).
- `pylindas/shared_dimension_queries/shared_dimensions_queries.py:23-37` — returns full JSON, defaults to TEST.

TEST/INT/PROD → URL `match` block duplicated in:

- `pylindas/lindas/query.py:5-11`
- `pylindas/getter/get.py:30-37` (`get_cube`) and `:72-79` (`get_observations`) — twice in one file
- `pylindas/shared_dimension_queries/shared_dimensions_queries.py:28-35`

Suggested home: `resolve_endpoint(environment)` + a generic
`run_query(query, environment, return_boolean=False)` in `lindas/query.py`.

## Cluster 6 — `_setup_graph()` namespace-binding loop (Medium)

- `pylindas/pycube/cube.py:222-240` — uses `Graph(bind_namespaces="none")`, binds cube namespace with trailing `/`.
- `pylindas/pyshareddimension/shared_dimension.py:154-165` — omits the custom-namespace bind.
- `pylindas/pycube/shared_dimension.py:18-33` (GeoSD) — **dead/buggy**: reads `self._cube_dict`, which is never set (class stores `self._description`).

Suggested home: `graph_utils.create_graph(base_uri=None, namespace_prefix=None)`.
Note: the GeoSD dead method removal is already covered by modernization
Requirement 4.

## Cluster 7 — `serialize()` + copy-pasted docstring (Low–Medium)

Identical body `self._graph.serialize(destination=filename, format="turtle", encoding="utf-8")`:

- `pylindas/pycube/cube.py:399-412` (returns `Self`)
- `pylindas/pyshareddimension/shared_dimension.py:390-402` (returns `Self`)
- `pylindas/pycube/shared_dimension.py:69-81` (returns `None`)

Copy-paste tell: all three docstrings say "Serialize the **cube** to a file,"
even in the two shared-dimension classes.
Suggested home: a mixin or `graph_utils.serialize_graph(graph, filename)`.

## Cluster 8 — URI construction (Low–Medium)

- `cube.py:189` (`rstrip("/")`), `:201-202` (`base + "/" + Identifier + "/" + Version`)
- `pyshareddimension/shared_dimension.py:137-141`, `:181-184`, `:195-196`

Divergence: only cube.py normalizes the trailing slash (issue #76); the SD paths
concatenate naively, so the #76 fix does not protect them.
Suggested home: `graph_utils.build_uri(base, *parts)` with normalization.

## Dead / unused code (intersects with duplication)

- `pylindas/pycube/shared_dimension.py` — stale `from py_cube...` import (`ModuleNotFoundError`); `GeoSharedDimension._setup_graph` dead and buggy. (Covered by modernization Req 4.)
- `pylindas/cli.py:5-11` — broken `py_cube` imports; CLI unusable. (Covered by modernization Req 2.)
- `pylindas/lindas/query.py:17-28` — `cube_exists()` unused; logic duplicated inline (Cluster 3).
- `pylindas/shared_dimension_queries/shared_dimensions_queries.py` — standalone script-style module, not imported by the package; overlaps `lindas/query.py` (Cluster 4).
