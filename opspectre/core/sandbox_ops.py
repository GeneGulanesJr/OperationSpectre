"""Sandbox lifecycle logic.

Pure execution layer — returns structured dicts, no console output.
Used by commands/sandbox.py (CLI) and mcp_server.py (MCP protocol).
"""

from typing import Any

from opspectre.core._runtime import get_runtime, reset_runtime
from opspectre.sandbox.docker_runtime import SandboxError


def sandbox_start() -> dict[str, Any]:
    """Start the sandbox container."""
    try:
        runtime = get_runtime()
        info = runtime.start()
        return {
            "success": True,
            "data": {
                "container_name": info.get("container_name"),
                "container_id": info.get("container_id"),
                "api_url": info.get("api_url"),
            },
            "error": None,
        }
    except SandboxError as e:
        return {"success": False, "data": {}, "error": e.message}


def sandbox_stop() -> dict[str, Any]:
    """Stop the sandbox container."""
    try:
        runtime = get_runtime()
        stopped = runtime.stop()
        reset_runtime()
        if stopped:
            return {"success": True, "data": {"status": "stopped"}, "error": None}
        return {"success": False, "data": {}, "error": "No sandbox running"}
    except SandboxError as e:
        return {"success": False, "data": {}, "error": e.message}


def sandbox_status() -> dict[str, Any]:
    """Get sandbox status."""
    try:
        runtime = get_runtime()
        status = runtime.status()
        return {
            "success": True,
            "data": {"status": status or "not_found"},
            "error": None,
        }
    except SandboxError as e:
        return {"success": False, "data": {}, "error": e.message}
