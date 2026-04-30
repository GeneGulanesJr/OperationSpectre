"""Browser automation commands.

These are the CLI-facing entry points. Each function takes a console object
for output. The actual browser logic lives in opspectre.core.browser_ops —
commands/ handles presentation (rich markup, JSON mode), core/ handles
execution and returns structured dicts.
"""

import json as _json
from typing import Any

from opspectre.sandbox.docker_runtime import DockerRuntime, SandboxError


def browser_navigate(console: Any, url: str) -> None:
    """Navigate browser to a URL."""
    from opspectre.performance import performance_logger

    with performance_logger.measure("browser_navigate", url=url):
        try:
            runtime = DockerRuntime()
            safe_url = _json.dumps(url)
            install_cmd = (
                'python3 -c "import subprocess; '
                "subprocess.run(['playwright', 'install', 'chromium'], "
                'capture_output=True)" 2>/dev/null; '
            )
            script_cmd = (
                'python3 -c "'
                "from playwright.sync_api import sync_playwright; "
                "p = sync_playwright().start(); "
                "b = p.chromium.launch(); "
                "page = b.new_page(); "
                f"page.goto({safe_url}); "
                "print(f'Navigated to {page.title()}'); "
                "b.close(); "
                'p.stop()"'
            )
            result = runtime.execute(f"{install_cmd}{script_cmd}", timeout=30)

            if result.get("stdout"):
                console.print(result["stdout"], end="")
            if result.get("stderr"):
                console.print(f"[red]{result['stderr']}[/]", end="")

            exit_code = result.get("exit_code", -1)
            if exit_code != 0:
                console.print(f"\n[dim]Exit code: {exit_code}[/]")
        except SandboxError as e:
            console.print(f"[red]Error: {e.message}[/]")
            if e.details:
                console.print(f"[dim]{e.details}[/]")


def browser_snapshot(console: Any) -> None:
    """Get page accessibility tree."""
    from opspectre.performance import performance_logger

    with performance_logger.measure("browser_snapshot"):
        console.print("[yellow]Browser snapshot - use navigate first[/]")


def browser_screenshot(console: Any, url: str) -> None:
    """Take a screenshot of a URL."""
    from opspectre.core.browser_ops import browser_screenshot as _screenshot
    from opspectre.performance import performance_logger

    with performance_logger.measure("browser_screenshot", url=url):
        try:
            result = _screenshot(url)
            if result.get("stdout"):
                console.print(result["stdout"], end="")
            if result.get("stderr"):
                console.print(f"[red]{result['stderr']}[/]", end="")
            if result.get("success"):
                path = result.get("data", {}).get("screenshot_path", "")
                if path:
                    console.print(f"\n[green]Screenshot saved: {path}[/]")
            exit_code = 0 if result.get("success") else -1
            if exit_code != 0:
                console.print(f"\n[dim]Exit code: {exit_code}[/]")
        except Exception as e:
            console.print(f"[red]Error: {e}[/]")
