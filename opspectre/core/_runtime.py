"""Cached DockerRuntime accessor for core modules.

Provides a single shared DockerRuntime instance to avoid reconnecting
on every tool call. Falls back to creating a fresh instance if the
cached one becomes stale.

DockerRuntime is lazy-imported so that importing opspectre.core does not
require the ``docker`` SDK at module-load time.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from opspectre.sandbox.docker_runtime import DockerRuntime

_runtime: Any = None  # DockerRuntime | None — resolved at runtime


def get_runtime() -> DockerRuntime:
    """Return a cached DockerRuntime instance, creating one if needed."""
    global _runtime
    if _runtime is None:
        from opspectre.sandbox.docker_runtime import DockerRuntime

        _runtime = DockerRuntime()
    return _runtime


def reset_runtime() -> None:
    """Discard the cached runtime (e.g. after sandbox stop)."""
    global _runtime
    _runtime = None
