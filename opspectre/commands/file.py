"""File operations."""

from typing import Any

from opspectre.core._runtime import get_runtime
from opspectre.sandbox.docker_runtime import SandboxError


def file_read(console: Any, path: str) -> None:
    """Read a file from the sandbox."""
    from opspectre.performance import performance_logger

    with performance_logger.measure("file_read_cmd", path=path):
        try:
            runtime = get_runtime()
            result = runtime.file_read(path)
            if result.get("success"):
                console.print(result.get("content", ""), end="")
            else:
                console.print(f"[red]Error: {result.get('error', 'Unknown error')}[/]")
        except SandboxError as e:
            console.print(f"[red]Error: {e.message}[/]")
            if e.details:
                console.print(f"[dim]{e.details}[/]")


def file_write(console: Any, path: str, content: str) -> None:
    """Write to a file in the sandbox."""
    from opspectre.performance import performance_logger

    with performance_logger.measure("file_write_cmd", path=path, content_size=len(content)):
        try:
            runtime = get_runtime()
            result = runtime.file_write(path, content)
            if result.get("success"):
                console.print(f"[green]Written to {path}[/]")
            else:
                console.print(f"[red]Error: {result.get('error', 'Unknown error')}[/]")
        except SandboxError as e:
            console.print(f"[red]Error: {e.message}[/]")
            if e.details:
                console.print(f"[dim]{e.details}[/]")


def file_edit(console: Any, path: str, old_text: str, new_text: str) -> None:
    """Find and replace in a file in the sandbox."""
    from opspectre.performance import performance_logger

    with performance_logger.measure(
        "file_edit_cmd", path=path,
        old_len=len(old_text), new_len=len(new_text)
    ):
        try:
            runtime = get_runtime()
            result = runtime.file_edit(path, old_text, new_text)
            if result.get("success"):
                console.print(f"[green]Replaced in {path}[/]")
            else:
                console.print(f"[red]Error: {result.get('error', 'Unknown error')}[/]")
        except SandboxError as e:
            console.print(f"[red]Error: {e.message}[/]")
            if e.details:
                console.print(f"[dim]{e.details}[/]")


def file_list(console: Any, path: str) -> None:
    """List directory contents in the sandbox."""
    from opspectre.performance import performance_logger

    with performance_logger.measure("file_list_cmd", path=path):
        try:
            runtime = get_runtime()
            result = runtime.file_list(path)
            if result.get("success"):
                console.print(result.get("data", result.get("content", "")))
            else:
                console.print(f"[red]Error: {result.get('error', 'Unknown error')}[/]")
        except SandboxError as e:
            console.print(f"[red]Error: {e.message}[/]")
            if e.details:
                console.print(f"[dim]{e.details}[/]")


def file_search(console: Any, pattern: str, path: str) -> None:
    """Search file contents in the sandbox."""
    from opspectre.performance import performance_logger

    with performance_logger.measure("file_search_cmd", query=pattern, path=path):
        try:
            runtime = get_runtime()
            result = runtime.file_search(pattern, path)
            if result.get("success"):
                data = result.get("data", result.get("content", ""))
                if data:
                    console.print(data)
                else:
                    console.print("[dim]No matches found[/]")
            else:
                console.print(f"[red]Error: {result.get('error', 'Unknown error')}[/]")
        except SandboxError as e:
            console.print(f"[red]Error: {e.message}[/]")
            if e.details:
                console.print(f"[dim]{e.details}[/]")
