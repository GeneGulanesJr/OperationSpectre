"""File operation logic.

All functions return dict: {"success": bool, "data": Any, "error": str|None}
"""

from typing import Any

from opspectre.core._runtime import get_runtime
from opspectre.sandbox.docker_runtime import SandboxError



def read_file(path: str) -> dict[str, Any]:
    """Read a file from the sandbox."""
    try:
        result = get_runtime().file_read(path)
        if result.get("success"):
            return {
                "success": True,
                "data": {"content": result.get("content", ""), "path": path},
                "error": None,
            }
        return {"success": False, "data": {}, "error": result.get("error", "Read failed")}
    except SandboxError as e:
        return {"success": False, "data": {}, "error": e.message}


def write_file(path: str, content: str) -> dict[str, Any]:
    """Write content to a file in the sandbox."""
    try:
        result = get_runtime().file_write(path, content)
        if result.get("success"):
            return {
                "success": True,
                "data": {"path": path, "bytes_written": len(content)},
                "error": None,
            }
        return {"success": False, "data": {}, "error": result.get("error", "Write failed")}
    except SandboxError as e:
        return {"success": False, "data": {}, "error": e.message}


def edit_file(path: str, old_text: str, new_text: str) -> dict[str, Any]:
    """Find and replace in a file."""
    try:
        result = get_runtime().file_edit(path, old_text, new_text)
        if result.get("success"):
            return {"success": True, "data": {"path": path}, "error": None}
        return {"success": False, "data": {}, "error": result.get("error", "Edit failed")}
    except SandboxError as e:
        return {"success": False, "data": {}, "error": e.message}


def list_directory(path: str = "/workspace") -> dict[str, Any]:
    """List directory contents."""
    try:
        result = get_runtime().file_list(path)
        if result.get("success"):
            return {
                "success": True,
                "data": result.get("data", result.get("content", "")),
                "error": None,
            }
        return {"success": False, "data": {}, "error": result.get("error", "List failed")}
    except SandboxError as e:
        return {"success": False, "data": {}, "error": e.message}


def search_files(pattern: str, path: str, recursive: bool = True) -> dict[str, Any]:
    """Search file contents.

    Args:
        pattern: Search pattern (regex supported).
        path: Directory or file to search in.
        recursive: Search recursively.
    """
    try:
        result = get_runtime().file_search(pattern, path)
        if result.get("success"):
            return {
                "success": True,
                "data": {"matches": result.get("data", result.get("content", ""))},
                "error": None,
            }
        return {"success": False, "data": {}, "error": result.get("error", "Search failed")}
    except SandboxError as e:
        return {"success": False, "data": {}, "error": e.message}
