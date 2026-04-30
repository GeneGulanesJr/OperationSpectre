"""Command handlers for the OPERATIONSPECTRE CLI.

This module decouples the CLI entry point (main.py) from individual
command implementations by centralising all handler imports and the
managed-sandbox context manager in one place.
"""

import argparse
import json
import os
from contextlib import contextmanager
from typing import Any

from opspectre._ui import _exit, _output_mode, console
from opspectre.config import Config

# ── Result presentation ──────────────────────────────────────────────

def _present_result(result: dict[str, Any]) -> None:
    """Format and print a shell/run result dict.

    Shared by cmd_shell and cmd_run to avoid duplicating the
    stdout/stderr/exit-code presentation logic.
    """
    if _output_mode.json_output:
        print(json.dumps(result, indent=2))
    else:
        if result.get("stdout"):
            console.print(result["stdout"], end="")
        if result.get("stderr"):
            console.print(f"[red]{result['stderr']}[/]", end="")
        exit_code = result.get("exit_code", -1)
        if exit_code != 0:
            console.print(f"\n[dim]Exit code: {exit_code}[/]")


def print_result(data: Any) -> None:
    """Print a result dict as JSON when --json-output is active, else as formatted text."""
    if _output_mode.json_output:
        print(json.dumps(data, indent=2, default=str))


def _report_run_error(e: Exception) -> None:
    """Format and print an error from a run command."""
    if _output_mode.json_output:
        print(json.dumps({"error": str(e), "exit_code": -1}, indent=2))
    else:
        console.print(f"[red]Error: {e}[/]")


# ── Sandbox helpers ──────────────────────────────────────────────────

def _ensure_sandbox() -> bool:
    """Start the sandbox if not already running. Returns True on success."""
    from opspectre.core._runtime import get_runtime
    from opspectre.sandbox.docker_runtime import SandboxError

    console.print("[dim]Starting sandbox...[/]")
    try:
        runtime = get_runtime()
        if runtime.status() == "running":
            console.print("[green]Sandbox already running[/]")
        else:
            info = runtime.start()
            console.print(f"[green]Sandbox started[/]  {info['container_name']}")
        return True
    except SandboxError as e:
        console.print(f"[red]Failed to start sandbox: {e.message}[/]")
        if e.details:
            console.print(f"[dim]{e.details}[/]")
        return False


@contextmanager
def _managed_sandbox():
    """Context manager that auto-starts sandbox if not running and cleans up after."""
    from opspectre.core._runtime import get_runtime, reset_runtime

    runtime = get_runtime()
    already_running = runtime.status() == "running"

    if not already_running:
        if not _output_mode.json_output:
            console.print("[dim]Starting sandbox...[/]")
        runtime.start()
    try:
        yield runtime
    finally:
        if not already_running:
            if not _output_mode.json_output:
                console.print("[dim]Cleaning up sandbox...[/]")
            runtime.stop()
            reset_runtime()


# ── Docker checks ────────────────────────────────────────────────────

def _check_docker_installed() -> bool:
    """Return True if Docker is installed, printing an error otherwise."""
    import shutil

    if shutil.which("docker") is None:
        console.print("[red]Docker is not installed.[/]")
        console.print("Install Docker Desktop: https://www.docker.com/products/docker-desktop/")
        return False
    console.print("[green]Docker found[/]")
    return True


def _check_docker_running():
    """Return a Docker client if the daemon is running, None otherwise."""
    from docker.errors import DockerException

    try:
        import docker

        client = docker.from_env(timeout=10)
        client.ping()
        console.print("[green]Docker daemon running[/]")
        return client
    except (DockerException, ConnectionError, TimeoutError):
        console.print("[red]Docker is not running.[/]")
        console.print("Start Docker Desktop and try again.")
        return None


def _ensure_image(client) -> bool:
    """Ensure the configured Docker image is available. Returns True on success."""
    from docker.errors import DockerException, ImageNotFound

    image_name = Config.get("opspectre_image")
    console.print(f"[dim]Checking image: {image_name}[/]")

    try:
        client.images.get(image_name)
        console.print("[green]Image found[/]")
        return True
    except (DockerException, ImageNotFound):
        console.print(
            f"[dim yellow]Pulling {image_name} (this may take a few minutes on first run)...[/]"
        )
        try:
            client.images.pull(image_name)
            console.print("[green]Image pulled[/]")
            return True
        except (DockerException, ImageNotFound) as e:
            console.print(f"[red]Failed to pull image: {e}[/]")
            return False


# ── Config helpers ────────────────────────────────────────────────────

def _validate_config_key(key: str) -> bool:
    """Return True if *key* is a valid Config key, printing an error otherwise."""
    if key not in Config._SCHEMA:
        console.print(f"[red]Unknown config key: {key!r}[/]")
        console.print(f"[dim]Valid keys: {', '.join(Config._SCHEMA.keys())}[/]")
        _exit(1)
        return False
    return True


def _config_set(args: argparse.Namespace) -> None:
    """Handle the 'config set' action."""
    from opspectre.config import ConfigError

    key = args.key
    if not _validate_config_key(key):
        return

    env_name = key.upper()
    prev = os.environ.pop(env_name, None)
    os.environ[env_name] = args.value
    try:
        schema_type = Config._SCHEMA[key][0]
        Config._typed_get(key, schema_type)
    except ConfigError as e:
        if prev is not None:
            os.environ[env_name] = prev
        else:
            os.environ.pop(env_name, None)
        console.print(f"[red]{e}[/]")
        _exit(1)
        return

    Config.save_current()
    console.print(f"[green]Set {key} = {args.value}[/]")


def _config_get(args: argparse.Namespace) -> None:
    """Handle the 'config get' action."""
    key = args.key
    if not _validate_config_key(key):
        return

    value = Config.get(key)
    if value:
        console.print(f"{key} = {value}")
    else:
        console.print(f"[dim]{key} is not set[/]")


# ── Command handlers ─────────────────────────────────────────────────

def cmd_init(args: argparse.Namespace) -> None:
    """Full setup: check Docker, pull image, start sandbox."""
    if not _check_docker_installed():
        return

    client = _check_docker_running()
    if client is None:
        return

    if not _ensure_image(client):
        return

    if not _ensure_sandbox():
        return

    console.print()
    console.print("[bold green]OPERATIONSPECTRE is ready.[/]")
    console.print()
    console.print('  opspectre run "ls -la"        # Run a command')
    console.print("  opspectre file read app.py     # Read a file")
    console.print('  opspectre shell "nmap target"  # Shell command')
    console.print()


def cmd_sandbox(args: argparse.Namespace) -> None:
    """Handle sandbox subcommands (start, stop, status)."""
    from opspectre.commands.sandbox import sandbox_start, sandbox_status, sandbox_stop

    if args.sandbox_action == "start":
        sandbox_start(console)
    elif args.sandbox_action == "stop":
        sandbox_stop(console)
    elif args.sandbox_action == "status":
        sandbox_status(console)
    else:
        console.print("[red]Unknown sandbox action. Use: start, stop, status[/]")
        _exit(1)
        return


def cmd_shell(args: argparse.Namespace) -> None:
    """Run a shell command inside the sandbox."""
    from opspectre.commands.shell import shell_run

    result = shell_run(console, args.shell_command, timeout=args.timeout)
    if result:
        _present_result(result)


def cmd_run(args: argparse.Namespace) -> None:
    """Run a command, auto-starting sandbox if needed, auto-cleanup after."""
    from opspectre.commands.shell import shell_run

    with _managed_sandbox():
        try:
            result = shell_run(console, args.run_command, timeout=args.timeout)
            if result:
                _present_result(result)
        except Exception as e:
            _report_run_error(e)


def cmd_file(args: argparse.Namespace) -> None:
    """Handle file subcommands (read, write, edit, list, search)."""
    from opspectre.commands.file import file_edit, file_list, file_read, file_search, file_write

    if args.file_action == "read":
        file_read(console, args.path)
    elif args.file_action == "write":
        file_write(console, args.path, args.content)
    elif args.file_action == "edit":
        file_edit(console, args.path, args.old, args.new)
    elif args.file_action == "list":
        file_list(console, args.path)
    elif args.file_action == "search":
        file_search(console, args.pattern, getattr(args, "path", "."))
    else:
        console.print("[red]Unknown file action. Use: read, write, edit, list, search[/]")
        _exit(1)
        return


def cmd_code(args: argparse.Namespace) -> None:
    """Execute code (Python or Node.js) inside the sandbox."""
    from opspectre.commands.code import code_run

    code_run(console, args.lang, args.target)


def cmd_browser(args: argparse.Namespace) -> None:
    """Handle browser subcommands (navigate, snapshot, screenshot)."""
    from opspectre.commands.browser import (
        browser_navigate,
        browser_screenshot,
        browser_snapshot,
    )

    if args.browser_action == "navigate":
        browser_navigate(console, args.url)
    elif args.browser_action == "snapshot":
        browser_snapshot(console)
    elif args.browser_action == "screenshot":
        browser_screenshot(console, args.url)
    else:
        console.print("[red]Unknown browser action. Use: navigate, snapshot, screenshot[/]")
        _exit(1)
        return


def cmd_performance(args: argparse.Namespace) -> None:
    """Handle performance analytics and monitoring."""
    from opspectre.commands.performance import (
        cmd_performance as _cmd_perf,
    )
    from opspectre.commands.performance import (
        cmd_performance_clear,
        cmd_performance_config,
    )

    action = getattr(args, "performance_action", None)

    if action == "config":
        import argparse as _ap

        config_args = _ap.Namespace(
            set=getattr(args, "set_key", None),
            value=getattr(args, "value", None),
            get=getattr(args, "get_key", None),
        )
        cmd_performance_config(config_args, console)
    elif action == "clear":
        import argparse as _ap

        clear_args = _ap.Namespace(
            operation=getattr(args, "operation", None),
        )
        cmd_performance_clear(clear_args, console)
    else:
        _cmd_perf(args, console)


def cmd_runs(args: argparse.Namespace) -> None:
    """Handle run history subcommands (list, show)."""
    from opspectre.reporting.run_manager import RunManager

    manager = RunManager()

    if args.runs_action == "list":
        runs = manager.list_runs()
        if not runs:
            console.print("[dim]No runs found[/]")
            return
        for run in runs:
            console.print(f"  {run['name']}  [dim]{run.get('status', 'unknown')}[/]")
    elif args.runs_action == "show":
        run = manager.get_run(args.run_name)
        if run:
            console.print(json.dumps(run, indent=2))
        else:
            console.print(f"[red]Run not found: {args.run_name}[/]")
    else:
        console.print("[red]Unknown runs action. Use: list, show[/]")
        _exit(1)
        return


def cmd_config(args: argparse.Namespace) -> None:
    """Handle configuration subcommands (set, get).

    Validates keys against _SCHEMA on set to prevent invalid values
    from being persisted.
    """
    if args.config_action == "set":
        _config_set(args)
    elif args.config_action == "get":
        _config_get(args)
    else:
        console.print("[red]Unknown config action. Use: set, get[/]")
        _exit(1)
