"""Custom exception hierarchy for already-existing LINDAS resources.

These replace ``sys.exit()`` calls in the non-local existence checks so that
library consumers receive catchable, non-terminating exceptions instead of a
terminated host process. Each exception carries the constructed URI (via
``.uri`` and the message) so callers can distinguish them from unrelated
failures.
"""


class ResourceExistsError(Exception):
    """Base: a resource already exists at the target URI in non-local mode."""

    def __init__(self, uri: str):
        self.uri = str(uri)
        super().__init__(
            f"Resource already exists at <{self.uri}>. Please update your YAML."
        )


class CubeAlreadyExistsError(ResourceExistsError):
    """Raised when a cube already exists at the constructed cube URI (local=False)."""

    def __init__(self, uri: str):
        self.uri = str(uri)
        super(ResourceExistsError, self).__init__(
            f"Cube already exists at <{self.uri}>. Please update your YAML."
        )


class SharedDimensionAlreadyExistsError(ResourceExistsError):
    """Raised when a shared dimension already exists at the constructed SD URI (local=False)."""

    def __init__(self, uri: str):
        self.uri = str(uri)
        super(ResourceExistsError, self).__init__(
            f"Shared Dimension already exists at <{self.uri}>. Please update your YAML."
        )
