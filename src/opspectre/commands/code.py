"""Code execution commands."""

import shlex
from typing import Any

from opspectre.sandbox.docker_runtime import DockerRuntime, SandboxError


def code_run(console: Any, lang: str, target: str) -> None:
    """Execute code in the sandbox."""
    from opspectre.performance import performance_logger

    with performance_logger.measure("code_run", lang=lang, target=target[:50] + "..."):
        try:
            runtime = DockerRuntime()
            safe_target = shlex.quote(target)

            if lang == "python":
                cmd = f"cd /workspace && python3 {safe_target}"
            elif lang == "node":
                cmd = f"cd /workspace && node {safe_target}"
            else:
                console.print(f"[red]Unsupported language: {lang}[/]")
                return

            result = runtime.execute(cmd)

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
