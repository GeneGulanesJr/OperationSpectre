"""Shell command execution."""

from typing import Any

from opspectre.sandbox.docker_runtime import SandboxError


def shell_run(console: Any, command: str, timeout: int | None = None) -> dict[str, Any] | None:
    """Run a shell command in the sandbox. Returns result dict."""
    from opspectre.core._runtime import get_runtime
    from opspectre.performance import performance_logger

    with performance_logger.measure("shell_run_cmd", command=command[:50] + "...", timeout=timeout):
        try:
            runtime = get_runtime()
            result = runtime.execute(command, timeout=timeout)

            stdout = result.get("stdout", "")
            stderr = result.get("stderr", "")
            exit_code = result.get("exit_code", -1)

            return {"stdout": stdout, "stderr": stderr, "exit_code": exit_code}
        except SandboxError as e:
            error_result = {"stdout": "", "stderr": e.message, "exit_code": -1}
            return error_result
