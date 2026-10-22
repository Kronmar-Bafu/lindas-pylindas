"""Path-safety helpers.

Centralizes validation of filesystem paths that originate from
user-supplied input (CLI arguments, downloaded dataset locations, etc.)
so that a single, auditable validator guards every file access.
"""

import os


class UnsafePathError(ValueError):
    """Raised when a resolved path escapes its permitted base directory."""


def reject_traversal(path: str, base_dir: str | None = None) -> None:
    """Validate ``path`` and raise if it performs a directory traversal.

    This is a pure *validator*: it returns nothing and never transforms the
    input. Callers keep using their own path variable for the actual file
    operation; this function's only effect is to raise on an unsafe value.
    Separating validation from the value this way makes the guard
    unambiguous for both humans and static taint analysis.

    An absolute ``path`` is accepted as an explicit, trusted choice. A
    relative ``path`` is resolved against ``base_dir`` (default: the current
    working directory) and must stay within it; one that climbs out via
    ``..`` is rejected.

    Args:
        path: The candidate path, possibly from untrusted input.
        base_dir: Directory a relative path must stay within. Defaults to
            the current working directory. Ignored for absolute paths.

    Raises:
        UnsafePathError: If the path is empty or a relative path escapes
            ``base_dir``.
    """
    if not path:
        raise UnsafePathError("Empty path is not allowed")

    if os.path.isabs(path):
        return

    base = os.path.realpath(base_dir if base_dir is not None else os.getcwd())
    resolved = os.path.realpath(os.path.join(base, path))

    if resolved != base and not resolved.startswith(base + os.sep):
        raise UnsafePathError(
            f"Path '{path}' escapes the permitted directory '{base}'"
        )
