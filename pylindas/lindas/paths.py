"""Path-safety helpers.

Centralizes validation of filesystem paths that originate from
user-supplied input (CLI arguments, downloaded dataset locations, etc.)
so that a single, auditable sanitizer guards every file access.
"""

import os


class UnsafePathError(ValueError):
    """Raised when a resolved path escapes its permitted base directory."""


def safe_path(path: str, base_dir: str | None = None) -> str:
    """Validate ``path`` against directory-traversal and return it normalized.

    This guards file access against path-traversal attacks. An absolute
    ``path`` is accepted as an explicit, trusted choice and simply
    normalized. A *relative* ``path`` is resolved against ``base_dir``
    (default: the current working directory) and must stay within it; a
    relative path that climbs out via ``..`` is rejected with
    :class:`UnsafePathError`.

    Args:
        path: The candidate path, possibly from untrusted input.
        base_dir: Directory a relative path must stay within. Defaults to
            the current working directory. Ignored for absolute paths.

    Returns:
        The validated, normalized, absolute path.

    Raises:
        UnsafePathError: If a relative path escapes ``base_dir``.
    """
    if not path:
        raise UnsafePathError("Empty path is not allowed")

    if os.path.isabs(path):
        # The caller explicitly supplied an absolute location; honor it.
        return os.path.normpath(path)

    base = os.path.realpath(base_dir if base_dir is not None else os.getcwd())
    resolved = os.path.realpath(os.path.join(base, path))

    # Containment check: a relative path must not climb out of base via "..".
    if resolved != base and not resolved.startswith(base + os.sep):
        raise UnsafePathError(
            f"Path '{path}' escapes the permitted directory '{base}'"
        )

    return resolved
