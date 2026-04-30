"""Browser automation logic.

All functions return dict: {"success": bool, "data": Any, "error": str|None}
"""

import json as _json
from typing import Any

from opspectre.core._runtime import get_runtime
from opspectre.sandbox.docker_runtime import SandboxError


def browser_navigate(url: str) -> dict[str, Any]:
    """Navigate browser to URL.

    Args:
        url: URL to navigate to.
    """
    try:
        runtime = get_runtime()
        install_cmd = (
            'python3 -c "import subprocess; '
            "subprocess.run(['playwright', 'install', 'chromium'], "
            'capture_output=True)" 2>/dev/null; '
        )
        safe_url = _json.dumps(url)
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

        stdout = result.get("stdout", "")
        stderr = result.get("stderr", "")
        exit_code = result.get("exit_code", -1)

        return {
            "success": exit_code == 0,
            "data": {"output": stdout, "url": url},
            "error": stderr if exit_code != 0 else None,
            "stdout": stdout,
            "stderr": stderr,
        }
    except SandboxError as e:
        return {"success": False, "data": {}, "error": e.message}


def browser_screenshot(
    url: str, output_path: str = "/workspace/output/screenshots/page.png"
) -> dict[str, Any]:
    """Take a browser screenshot of a URL.

    Args:
        url: URL to navigate to and screenshot.
        output_path: Path to save the screenshot (inside sandbox).
    """
    try:
        runtime = get_runtime()
        install_cmd = (
            'python3 -c "import subprocess; '
            "subprocess.run(['playwright', 'install', 'chromium'], "
            'capture_output=True)" 2>/dev/null; '
        )
        safe_url = _json.dumps(url)
        safe_output = _json.dumps(output_path)
        script_cmd = (
            'python3 -c "'
            "import os; "
            "from playwright.sync_api import sync_playwright; "
            "p = sync_playwright().start(); "
            "b = p.chromium.launch(); "
            "page = b.new_page(); "
            f"page.goto({safe_url}); "
            f"os.makedirs(os.path.dirname({safe_output}), exist_ok=True); "
            f"page.screenshot(path={safe_output}, full_page=True); "
            f"print(f'Screenshot saved to {safe_output}'); "
            "b.close(); "
            'p.stop()"'
        )
        result = runtime.execute(f"{install_cmd}{script_cmd}", timeout=30)

        stdout = result.get("stdout", "")
        stderr = result.get("stderr", "")
        exit_code = result.get("exit_code", -1)

        return {
            "success": exit_code == 0,
            "data": {"output": stdout, "url": url, "screenshot_path": output_path},
            "error": stderr if exit_code != 0 else None,
            "stdout": stdout,
            "stderr": stderr,
        }
    except SandboxError as e:
        return {"success": False, "data": {}, "error": e.message}
