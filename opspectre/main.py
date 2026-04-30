"""OPERATIONSPECTRE CLI entry point."""

import argparse
from typing import Any

from opspectre._ui import _exit, _output_mode, console
from opspectre.cli_commands import (
    cmd_browser,
    cmd_code,
    cmd_config,
    cmd_file,
    cmd_init,
    cmd_performance,
    cmd_run,
    cmd_runs,
    cmd_sandbox,
    cmd_shell,
)
from opspectre.config import Config

Config.apply_saved()


def get_version() -> str:
    try:
        from opspectre import __version__

        return __version__
    except Exception:
        return "0.1.0"


# ── Parser builders ──────────────────────────────────────────────────

def _build_sandbox_parser(subparsers: argparse._SubParsersAction) -> None:
    """Register the 'sandbox' subcommand."""
    p = subparsers.add_parser("sandbox", help="Manage sandbox container")
    p.add_argument("sandbox_action", choices=["start", "stop", "status"], help="Sandbox action")


def _build_shell_parser(subparsers: argparse._SubParsersAction) -> None:
    """Register the 'shell' subcommand."""
    p = subparsers.add_parser("shell", help="Run shell command in sandbox")
    p.add_argument("shell_command", help="Shell command to execute")
    p.add_argument("--timeout", type=int, default=None, help="Timeout in seconds")


def _build_run_parser(subparsers: argparse._SubParsersAction) -> None:
    """Register the 'run' subcommand."""
    p = subparsers.add_parser("run", help="Run command (auto-starts sandbox if needed)")
    p.add_argument("run_command", help="Command to execute")
    p.add_argument("--timeout", type=int, default=None, help="Timeout in seconds")


def _build_file_parser(subparsers: argparse._SubParsersAction) -> None:
    """Register the 'file' subcommand with its nested actions."""
    p = subparsers.add_parser("file", help="File operations")
    sub = p.add_subparsers(dest="file_action")

    r = sub.add_parser("read", help="Read a file")
    r.add_argument("path", help="File path")

    w = sub.add_parser("write", help="Write to a file")
    w.add_argument("path", help="File path")
    w.add_argument("content", help="Content to write")

    e = sub.add_parser("edit", help="Find and replace in file")
    e.add_argument("path", help="File path")
    e.add_argument("old", help="Text to find")
    e.add_argument("new", help="Replacement text")

    lst = sub.add_parser("list", help="List directory")
    lst.add_argument("path", nargs="?", default="/workspace", help="Directory path")

    s = sub.add_parser("search", help="Search file contents")
    s.add_argument("pattern", help="Search pattern")
    s.add_argument("path", nargs="?", default=".", help="Search path")


def _build_code_parser(subparsers: argparse._SubParsersAction) -> None:
    """Register the 'code' subcommand."""
    p = subparsers.add_parser("code", help="Execute code")
    p.add_argument("lang", choices=["python", "node"], help="Language")
    p.add_argument("target", help="File path or inline code")


def _build_browser_parser(subparsers: argparse._SubParsersAction) -> None:
    """Register the 'browser' subcommand with its nested actions."""
    p = subparsers.add_parser("browser", help="Browser automation")
    sub = p.add_subparsers(dest="browser_action")

    nav = sub.add_parser("navigate", help="Navigate to URL")
    nav.add_argument("url", help="URL to navigate to")

    sub.add_parser("snapshot", help="Get page accessibility tree")

    ss = sub.add_parser("screenshot", help="Take a screenshot of a URL")
    ss.add_argument("url", help="URL to screenshot")


def _build_runs_parser(subparsers: argparse._SubParsersAction) -> None:
    """Register the 'runs' subcommand with its nested actions."""
    p = subparsers.add_parser("runs", help="Manage run history")
    sub = p.add_subparsers(dest="runs_action")

    sub.add_parser("list", help="List all runs")

    show = sub.add_parser("show", help="Show run details")
    show.add_argument("run_name", help="Run name")


def _build_config_parser(subparsers: argparse._SubParsersAction) -> None:
    """Register the 'config' subcommand with its nested actions."""
    p = subparsers.add_parser("config", help="Manage configuration")
    sub = p.add_subparsers(dest="config_action")

    s = sub.add_parser("set", help="Set config value")
    s.add_argument("key", help="Config key")
    s.add_argument("value", help="Config value")

    g = sub.add_parser("get", help="Get config value")
    g.add_argument("key", help="Config key")


def _build_performance_parser(subparsers: argparse._SubParsersAction) -> None:
    """Register the 'performance' subcommand with its nested actions."""
    p = subparsers.add_parser("performance", help="Performance analytics and monitoring")
    sub = p.add_subparsers(dest="performance_action")

    sub.add_parser("show", help="Show performance analytics (default)")
    sub.add_parser("stats", help="Show performance analytics")

    cfg = sub.add_parser("config", help="Configure performance monitoring")
    cfg.add_argument("--set", dest="set_key", help="Config key to set")
    cfg.add_argument("--value", help="Value to set (use with --set)")
    cfg.add_argument("--get", dest="get_key", help="Config key to get")

    clr = sub.add_parser("clear", help="Clear performance metrics")
    clr.add_argument("--operation", help="Clear metrics for specific operation only")

    p.add_argument("--export", choices=["json", "csv"], help="Export metrics data")


def _build_parser() -> argparse.ArgumentParser:
    """Build and return the fully-configured argument parser."""
    parser = argparse.ArgumentParser(
        prog="opspectre",
        description="OPERATIONSPECTRE - CLI toolbox for sandboxed tool execution",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )

    parser.add_argument("-v", "--version", action="version", version=f"opspectre {get_version()}")
    parser.add_argument("--json-output", action="store_true", help="Output results as JSON")
    parser.add_argument("--timeout", type=int, default=None, help="Command timeout in seconds")

    subparsers = parser.add_subparsers(dest="command", help="Available commands")

    subparsers.add_parser("init", help="Full setup: check Docker, pull image, start sandbox")
    _build_sandbox_parser(subparsers)
    _build_shell_parser(subparsers)
    _build_run_parser(subparsers)
    _build_file_parser(subparsers)
    _build_code_parser(subparsers)
    _build_browser_parser(subparsers)
    _build_runs_parser(subparsers)
    _build_config_parser(subparsers)
    _build_performance_parser(subparsers)

    return parser


# ── Dispatch ─────────────────────────────────────────────────────────

def _dispatch(args: argparse.Namespace) -> None:
    """Route parsed args to the appropriate command handler."""
    command_map: dict[str, Any] = {
        "init": cmd_init,
        "run": cmd_run,
        "sandbox": cmd_sandbox,
        "shell": cmd_shell,
        "file": cmd_file,
        "code": cmd_code,
        "browser": cmd_browser,
        "runs": cmd_runs,
        "config": cmd_config,
        "performance": cmd_performance,
    }

    handler = command_map.get(args.command)
    if not handler:
        return

    try:
        handler(args)
    except Exception as e:
        from opspectre.sandbox.docker_runtime import SandboxError

        if isinstance(e, SandboxError) and e.details:
            console.print(f"[red]Error: {e.message}[/]")
            console.print(f"[dim]{e.details}[/]")
        else:
            console.print(f"[red]Error: {e}[/]")
        _exit(1)


def main() -> None:
    """CLI entry point — parse arguments and dispatch to command handlers."""
    parser = _build_parser()
    args = parser.parse_args()

    _output_mode.json_output = args.json_output

    if not args.command:
        parser.print_help()
        _exit(1)
        return

    _dispatch(args)
