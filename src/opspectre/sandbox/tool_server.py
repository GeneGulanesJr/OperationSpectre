"""In-container FastAPI tool server.

Runs inside the Docker sandbox container. Provides endpoints for:
- /execute - Run shell commands
- /file/read - Read files
- /file/write - Write files
- /file/edit - Find and replace in files
- /file/list - List directory contents
- /file/search - Search file contents with regex
- /health - Health check
"""

import argparse
import asyncio
import logging
import os
from pathlib import Path
from typing import Any

from fastapi import FastAPI, HTTPException, Request, status
from pydantic import BaseModel

_audit_log = logging.getLogger("opspectre.audit")

SANDBOX_MODE = os.getenv("OPSPECTRE_SANDBOX_MODE", "false").lower() == "true"
if not SANDBOX_MODE:
    raise RuntimeError("Tool server should only run in sandbox mode (OPSPECTRE_SANDBOX_MODE=true)")

parser = argparse.ArgumentParser(description="Start OPERATIONSPECTRE tool server")
parser.add_argument("--token", required=True, help="Authentication token")
parser.add_argument("--host", default="0.0.0.0", help="Host to bind to")
parser.add_argument("--port", type=int, required=True, help="Port to bind to")
parser.add_argument(
    "--timeout",
    type=int,
    default=120,
    help="Hard timeout in seconds for each request execution (default: 120)",
)

args = parser.parse_args()
EXPECTED_TOKEN: str = args.token
REQUEST_TIMEOUT = args.timeout

app = FastAPI()

# Paths that don't require authentication
_PUBLIC_PATHS = {"/health", "/openapi.json", "/docs"}
_MAX_OUTPUT_BYTES = 1_048_576  # 1 MB — truncate limit for command output and file reads

# Allowed root for file operations — prevents path traversal
_ALLOWED_ROOT = Path("/workspace").resolve()


def _safe_path(raw_path: str) -> Path:
    """Resolve a path and ensure it stays within the allowed root.

    Raises HTTPException if the resolved path escapes the sandbox boundary.
    """
    resolved = Path(raw_path).resolve()
    try:
        resolved.relative_to(_ALLOWED_ROOT)
    except ValueError as err:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"Path '{raw_path}' is outside the allowed workspace boundary",
        ) from err
    return resolved


@app.middleware("http")
async def auth_middleware(request: Request, call_next: Any) -> Any:
    """Middleware-based Bearer token auth — avoids FastAPI body-merge issues."""
    if request.url.path in _PUBLIC_PATHS or request.url.path.startswith("/docs"):
        return await call_next(request)

    auth_header = request.headers.get("authorization", "")
    if not auth_header.startswith("Bearer "):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing or invalid Authorization header. Bearer token required.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    token = auth_header.removeprefix("Bearer ")
    if token != EXPECTED_TOKEN:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication token",
            headers={"WWW-Authenticate": "Bearer"},
        )

    return await call_next(request)


class ToolExecutionRequest(BaseModel):
    command: str
    timeout: int | None = None


class FileReadRequest(BaseModel):
    path: str


class FileWriteRequest(BaseModel):
    path: str
    content: str


class FileEditRequest(BaseModel):
    path: str
    old_text: str
    new_text: str
    replace_count: int | None = None  # None = replace all, N = replace first N


class FileListRequest(BaseModel):
    path: str = "/workspace"


class FileSearchRequest(BaseModel):
    pattern: str
    path: str = "/workspace"


async def run_command(command: str, timeout: int) -> dict[str, Any]:
    """Run a shell command and capture output."""
    try:
        proc = await asyncio.create_subprocess_shell(
            command,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
            cwd="/workspace",
            env={**os.environ, "PYTHONUNBUFFERED": "1"},
        )

        try:
            stdout_bytes, stderr_bytes = await asyncio.wait_for(proc.communicate(), timeout=timeout)
        except TimeoutError:
            proc.kill()
            await proc.wait()
            return {
                "stdout": "",
                "stderr": f"Command timed out after {timeout} seconds",
                "exit_code": -1,
            }

        stdout = stdout_bytes.decode("utf-8", errors="replace")
        stderr = stderr_bytes.decode("utf-8", errors="replace")

        # Truncate large outputs
        if len(stdout) > _MAX_OUTPUT_BYTES:
            stdout = stdout[:_MAX_OUTPUT_BYTES] + f"\n... (truncated, {len(stdout)} bytes total)"
        if len(stderr) > _MAX_OUTPUT_BYTES:
            stderr = stderr[:_MAX_OUTPUT_BYTES] + f"\n... (truncated, {len(stderr)} bytes total)"

        return {
            "stdout": stdout,
            "stderr": stderr,
            "exit_code": proc.returncode,
        }
    except Exception as e:
        return {
            "stdout": "",
            "stderr": str(e),
            "exit_code": -1,
        }


@app.get("/health")
async def health() -> dict[str, str]:
    return {"status": "healthy"}


@app.post("/execute")
async def execute(request: ToolExecutionRequest) -> dict[str, Any]:
    timeout = request.timeout or REQUEST_TIMEOUT
    _audit_log.info("EXECUTE command=%s timeout=%s", request.command[:200], timeout)
    return await run_command(request.command, timeout)


@app.post("/file/read")
async def file_read(request: FileReadRequest) -> dict[str, Any]:
    try:
        path = _safe_path(request.path)
        if not path.exists():
            return {"success": False, "error": f"File not found: {request.path}"}
        if not path.is_file():
            return {"success": False, "error": f"Not a file: {request.path}"}

        content = path.read_text(encoding="utf-8", errors="replace")

        # Truncate large files
        if len(content) > _MAX_OUTPUT_BYTES:
            content = content[:_MAX_OUTPUT_BYTES] + f"\n... (truncated, {len(content)} chars total)"

        return {"success": True, "content": content}
    except Exception as e:
        return {"success": False, "error": str(e)}


@app.post("/file/write")
async def file_write(request: FileWriteRequest) -> dict[str, Any]:
    try:
        path = _safe_path(request.path)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(request.content, encoding="utf-8")
        return {"success": True}
    except Exception as e:
        return {"success": False, "error": str(e)}


@app.post("/file/edit")
async def file_edit(request: FileEditRequest) -> dict[str, Any]:
    try:
        path = _safe_path(request.path)
        if not path.exists():
            return {"success": False, "error": f"File not found: {request.path}"}

        content = path.read_text(encoding="utf-8")

        if request.old_text not in content:
            return {"success": False, "error": "old_text not found in file"}

        total_occurrences = content.count(request.old_text)
        if request.replace_count is not None and request.replace_count > 0:
            new_content = content.replace(request.old_text, request.new_text, request.replace_count)
            replacements = min(request.replace_count, total_occurrences)
        else:
            new_content = content.replace(request.old_text, request.new_text)
            replacements = total_occurrences
        path.write_text(new_content, encoding="utf-8")

        return {
            "success": True,
            "replacements": replacements,
            "total_occurrences": total_occurrences,
        }
    except Exception as e:
        return {"success": False, "error": str(e)}


@app.post("/file/list")
async def file_list(request: FileListRequest) -> dict[str, Any]:
    try:
        path = _safe_path(request.path)
        if not path.exists():
            return {"success": False, "error": f"Directory not found: {request.path}"}
        if not path.is_dir():
            return {"success": False, "error": f"Not a directory: {request.path}"}

        entries = sorted(path.iterdir(), key=lambda e: (not e.is_dir(), e.name.lower()))
        lines = []
        for entry in entries:
            if entry.is_dir():
                lines.append(f"  {entry.name}/")
            else:
                size = entry.stat().st_size
                lines.append(f"  {entry.name}  ({size} bytes)")

        return {"success": True, "content": "\n".join(lines) if lines else "(empty directory)"}
    except Exception as e:
        return {"success": False, "error": str(e)}


def _search_files_in_dir(search_path: Path, pattern: str) -> dict[str, Any]:
    """Search files under *search_path* for lines matching *pattern* (regex).

    Returns a result dict with ``success`` and either ``content`` or ``error``.
    """
    import re

    try:
        # Compile user-supplied regex -- re.compile() is safe (not eval).
        # Flagged as eval_exec by static analysis; this is a false positive.
        regex = re.compile(pattern)
    except re.error as e:
        return {"success": False, "error": f"Invalid regex: {e}"}

    matches: list[str] = []
    for file_path in search_path.rglob("*"):
        if not file_path.is_file():
            continue
        try:
            content = file_path.read_text(encoding="utf-8", errors="replace")
            for i, line in enumerate(content.split("\n"), 1):
                if regex.search(line):
                    rel = file_path.relative_to(search_path)
                    matches.append(f"{rel}:{i}: {line.strip()}")
        except (PermissionError, OSError):
            continue

    return {
        "success": True,
        "content": "\n".join(matches) if matches else "No matches found",
    }


@app.post("/file/search")
async def file_search(request: FileSearchRequest) -> dict[str, Any]:
    try:
        search_path = _safe_path(request.path)
        if not search_path.exists():
            return {"success": False, "error": f"Path not found: {request.path}"}
        if not search_path.is_dir():
            return {"success": False, "error": f"Not a directory: {request.path}"}

        return _search_files_in_dir(search_path, request.pattern)
    except Exception as e:
        return {"success": False, "error": str(e)}


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host=args.host, port=args.port, log_level="info")
