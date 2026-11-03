"""Upload Turtle files to a LINDAS triplestore (GraphDB).

LINDAS migrated from Stardog to GraphDB. GraphDB implements the SPARQL 1.1
Graph Store HTTP Protocol, so uploads are plain authenticated HTTP requests
against the repository's graph-store service rather than a Stardog-specific
client connection:

* append Turtle to a named graph -> ``POST`` with ``Content-Type: text/turtle``
* replace a named graph           -> ``PUT``
* clear a named graph             -> ``DELETE``

Connection details are read from a ``lindas.ini`` section (selected by
``environment``) containing at least an ``endpoint`` and, for a protected
store, ``username`` / ``password``. Example:

    [TEST]
    endpoint=https://graphdb.test.cz-aws.net/repositories/lindas/rdf-graphs/service
    username=a-lindas-user-name
    password=...
"""

from configparser import ConfigParser
from typing import Union

import requests
from requests.auth import HTTPBasicAuth


def _load_config(db_file: str, environment: str) -> dict:
    parser = ConfigParser()
    parser.read(db_file)

    config = {}
    if parser.has_section(environment):
        params = parser.items(environment)
        for param in params:
            config[param[0]] = param[1]
    else:
        raise Exception(f"Environment '{environment}' not found in db_file")

    return config


def _auth_from_config(config: dict) -> Union[HTTPBasicAuth, None]:
    """Build basic-auth from the config, or ``None`` when no credentials given."""
    username = config.get("username")
    password = config.get("password")
    if username and password:
        return HTTPBasicAuth(username, password)
    return None


def upload_ttl(
    filename: Union[str, list],
    db_file: str,
    environment: str,
    graph_uri: str,
    clear_graph: bool = False,
):
    """Upload one or more Turtle files into a GraphDB named graph.

    Uses the SPARQL 1.1 Graph Store HTTP Protocol. All files are appended to
    ``graph_uri``; when ``clear_graph`` is set, the named graph is emptied first.

    Args:
        filename: Path to a Turtle file, or a list of paths.
        db_file: Path to the ``lindas.ini`` holding endpoint/credentials.
        environment: Section name in ``lindas.ini`` (e.g. ``TEST``).
        graph_uri: Target named graph IRI.
        clear_graph: When True, delete the named graph before adding (requires
            ``graph_uri`` so the whole store is never cleared by accident).
    """
    config = _load_config(db_file, environment)

    endpoint = config.get("endpoint")
    if not endpoint:
        raise Exception(
            f"No 'endpoint' configured for environment '{environment}' in {db_file}"
        )

    auth = _auth_from_config(config)
    params = {"graph": graph_uri}

    if clear_graph and graph_uri:
        # Guard: only clear when a specific graph is given, so we never wipe the
        # whole store. Mirrors the old connection-based safety check.
        resp = requests.delete(endpoint, params=params, auth=auth)
        resp.raise_for_status()

    def _add_file(file: str):
        print(f"uploading: {file}")
        with open(file, "rb") as f:
            resp = requests.post(
                endpoint,
                params=params,
                headers={"Content-Type": "text/turtle"},
                data=f,
                auth=auth,
            )
        resp.raise_for_status()

    files = [filename] if isinstance(filename, str) else filename
    for f in files:
        _add_file(file=f)
