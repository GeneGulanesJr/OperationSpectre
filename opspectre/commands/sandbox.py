"""Sandbox lifecycle commands.

CLI-facing entry points that delegate to opspectre.core._runtime (DockerRuntime).
commands/ handles console presentation; core/ returns structured dicts for
programmatic use (Docker sandbox, pipelines).
"""

from typing import Any

from opspectre.core._runtime import get_runtime, reset_runtime
from opspectre.sandbox.docker_runtime import SandboxError


def sandbox_start(console: Any) -> None:
    """Start the sandbox container."""
    try:
        runtime = get_runtime()
        console.print("[dim]Starting sandbox container...[/]")
        info = runtime.start()
        console.print(f"[green]Sandbox started[/]  {info['container_name']}")
    except SandboxError as e:
        console.print(f"[red]Failed to start sandbox: {e.message}[/]")
        if e.details:
            console.print(f"[dim]{e.details}[/]")


def sandbox_stop(console: Any) -> None:
    """Stop the sandbox container."""
    try:
        runtime = get_runtime()
        if runtime.stop():
            reset_runtime()
            console.print("[green]Sandbox stopped[/]")
        else:
            console.print("[yellow]No sandbox running[/]")
    except SandboxError as e:
        console.print(f"[red]Error: {e.message}[/]")
        if e.details:
            console.print(f"[dim]{e.details}[/]")


def sandbox_status(console: Any) -> None:
    """Check sandbox status."""
    try:
        runtime = get_runtime()
        status = runtime.status()
        if status == "running":
            console.print("[green]Sandbox is running[/]")
        elif status:
            console.print(f"[yellow]Sandbox is {status}[/]")
        else:
            console.print("[dim]No sandbox found[/]")
    except SandboxError as e:
        console.print(f"[red]Error: {e.message}[/]")
        if e.details:
            console.print(f"[dim]{e.details}[/]")
