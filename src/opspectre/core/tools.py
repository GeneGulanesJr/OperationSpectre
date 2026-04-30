"""Security and scanning tool logic.

All functions return dict: {"success": bool, "data": Any, "error": str|None}
No console output — callers handle presentation.
All executions are logged via ExecutionLogger.
"""

import secrets
import shlex
from typing import Any

from opspectre.core._runtime import get_runtime
from opspectre.core.execution_log import exec_logger, summarize_output
from opspectre.sandbox.docker_runtime import SandboxError

# Default timeouts (seconds)
DEFAULT_TOOL_TIMEOUT = 120
LONG_TOOL_TIMEOUT = 300

# Scan defaults
HTTP_PROBE_RATE_LIMIT = 5
NUCLEI_RATE_LIMIT = 15
NUCLEI_CONCURRENCY = 5
NUCLEI_TIMEOUT = 15

# Output limits
OUTPUT_SUMMARY_MAX_LINES = 3
OUTPUT_SUMMARY_MAX_CHARS = 120

# Code execution
HEREDOC_TOKEN_BYTES = 8


def _exec_and_log(
    tool: str,
    target: str,
    params: dict[str, Any],
    command: str,
    timeout: int | None = None,
) -> dict[str, Any]:
    """Execute a command and log the result. Central helper for all tools."""
    ctx = exec_logger.start(tool, target, params)
    try:
        runtime = get_runtime()
        result = runtime.execute(command, timeout=timeout)
        stdout = result.get("stdout", "")
        stderr = result.get("stderr", "")
        exit_code = result.get("exit_code", -1)
        summary = summarize_output(tool, stdout)
        success = exit_code == 0
        exec_logger.finish(
            ctx, success=success, stdout=stdout, stderr=stderr,
            exit_code=exit_code, findings_summary=summary,
        )

        if success:
            return {
                "success": True,
                "data": {"output": stdout, "raw_output": stdout},
                "error": None,
                "stdout": stdout,
                "stderr": stderr,
            }
        # Non-zero exit code, but return stdout if present (some tools emit partial results)
        return {
            "success": False,
            "data": {"output": stdout, "raw_output": stdout} if stdout.strip() else {},
            "error": stderr or "Command failed",
            "stdout": stdout,
            "stderr": stderr,
        }
    except SandboxError as e:
        exec_logger.finish(ctx, success=False, error=e.message)
        return {"success": False, "data": {}, "error": e.message}


def execute_shell(command: str, timeout: int | None = None) -> dict[str, Any]:
    """Run an arbitrary shell command in the sandbox."""
    return _exec_and_log("shell_execute", command[:80], {"command": command}, command, timeout)


def run_nmap_scan(
    target: str,
    ports: str | None = None,
    stealth: bool = False,
    service_detect: bool = True,
) -> dict[str, Any]:
    """Run nmap scan."""
    safe_target = shlex.quote(target)
    cmd = "nmap"
    if service_detect:
        cmd += " -sV"
    if ports:
        cmd += f" -p {shlex.quote(ports)}"
    if stealth:
        cmd += " -T2 --max-retries 2 --host-timeout 10m"
    cmd += f" {safe_target}"
    params = {
        "ports": ports, "stealth": stealth, "service_detect": service_detect
    }
    return _exec_and_log("nmap_scan", target, params, cmd)


def discover_subdomains(domain: str, method: str = "subfinder") -> dict[str, Any]:
    """Find subdomains."""
    safe_domain = shlex.quote(domain)
    commands = {
        "subfinder": f"subfinder -d {safe_domain}",
        "crt": f"osint_ct_subdomains {safe_domain}",
        "full_passive": f"osint_full_passive {safe_domain}",
    }
    cmd = commands.get(method, f"subfinder -d {safe_domain}")
    return _exec_and_log("subdomain_discovery", domain, {"method": method}, cmd)


def probe_http(
    targets: str | list[str], rate_limit: int = HTTP_PROBE_RATE_LIMIT,
) -> dict[str, Any]:
    """Probe HTTP targets with httpx."""
    if isinstance(targets, list):
        targets_str = "\n".join(targets)
        target_summary = f"{len(targets)} targets"
        quoted = shlex.quote(targets_str)
        cmd = (
            f"echo {quoted} | httpx -status-code -title "
            f"-tech-detect -rate-limit {rate_limit}"
        )
    else:
        target_summary = targets
        quoted = shlex.quote(targets)
        cmd = (
            f"httpx -status-code -title -tech-detect "
            f"-rate-limit {rate_limit} {quoted}"
        )
    num_targets = len(targets) if isinstance(targets, list) else 1
    params = {"rate_limit": rate_limit, "num_targets": num_targets}
    return _exec_and_log("http_probe", target_summary, params, cmd)


def scan_nuclei(
    targets: str | list[str],
    severity: str = "medium,high,critical",
    rate_limit: int = NUCLEI_RATE_LIMIT,
    concurrency: int = NUCLEI_CONCURRENCY,
) -> dict[str, Any]:
    """Run nuclei vulnerability scan."""
    if isinstance(targets, list):
        targets_file = "/tmp/nuclei_targets.txt"
        targets_str = "\n".join(targets)
        target_summary = f"{len(targets)} targets"
        cmd = (
            f"echo {shlex.quote(targets_str)} > {targets_file} && "
            f"nuclei -l {targets_file} "
            f"-severity {shlex.quote(severity)} -rl {rate_limit} -c {concurrency} "
            f"-timeout {NUCLEI_TIMEOUT} -retries 2"
        )
    else:
        target_summary = targets
        cmd = (
            f"nuclei -u {shlex.quote(targets)} "
            f"-severity {shlex.quote(severity)} -rl {rate_limit} -c {concurrency} "
            f"-timeout {NUCLEI_TIMEOUT} -retries 2"
        )
    nuclei_params = {
        "severity": severity, "rate_limit": rate_limit, "concurrency": concurrency
    }
    return _exec_and_log(
        "nuclei_scan", target_summary, nuclei_params, cmd, timeout=LONG_TOOL_TIMEOUT
    )


def gowitness_capture(
    targets: str | list[str],
    output_dir: str = "/workspace/output/screenshots",
) -> dict[str, Any]:
    """Take screenshots with gowitness."""
    if isinstance(targets, list):
        targets_file = "/tmp/gowitness_targets.txt"
        targets_str = "\n".join(targets)
        target_summary = f"{len(targets)} targets"
        cmd = (
            f"echo {shlex.quote(targets_str)} > {targets_file} && "
            f"cat {targets_file} | gowitness file - -P {shlex.quote(output_dir)}"
        )
    else:
        target_summary = targets
        quoted = shlex.quote(targets)
        cmd = (
            f"echo {quoted} | gowitness file - "
            f"-P {shlex.quote(output_dir)}"
        )
    return _exec_and_log(
        "gowitness_screenshots", target_summary,
        {"output_dir": output_dir}, cmd, timeout=LONG_TOOL_TIMEOUT
    )


def osint_recon(domain: str, method: str = "full") -> dict[str, Any]:
    """Run passive OSINT."""
    safe_domain = shlex.quote(domain)
    commands = {
        "ct": f"osint_ct_subdomains {safe_domain}",
        "wayback": f"osint_wayback_urls {safe_domain}",
        "google": f"osint_google_dorks {safe_domain}",
        "shodan": f"osint_shodan_queries {safe_domain}",
        "full": f"osint_full_passive {safe_domain}",
    }
    cmd = commands.get(method, f"osint_full_passive {safe_domain}")
    return _exec_and_log("osint_recon", domain, {"method": method}, cmd)


def port_scan(
    target: str,
    scan_type: str = "quick",
    ports: str | None = None,
) -> dict[str, Any]:
    """Run port scan with predefined profiles."""
    safe_target = shlex.quote(target)
    profiles = {
        "quick": "-sV -sC -T4 -F",
        "full": "-sV -sC -T4 -p-",
        "stealth": None,
        "service": "-sV -sC -T4 -p 80,443,8080,8443",
    }
    if scan_type == "stealth":
        cmd = f"stealth_nmap {safe_target}"
    else:
        flags = profiles.get(scan_type, "-sV -sC -T4")
        port_flag = f" -p {shlex.quote(ports)}" if ports else ""
        cmd = f"nmap {flags}{port_flag} {safe_target}"
    return _exec_and_log("port_scan", target, {"scan_type": scan_type, "ports": ports}, cmd)


def wpscan_scan(url: str) -> dict[str, Any]:
    """Run WordPress vulnerability scan."""
    from urllib.parse import urlparse

    safe_url = shlex.quote(url)
    parsed = urlparse(url if "://" in url else f"http://{url}")
    domain = parsed.hostname or url.split("/")[0]
    safe_domain = shlex.quote(domain)
    cmd = (
        f"wpscan --url {safe_url} --enumerate u,vp,vt "
        f"--random-user-agent --disable-tls-checks "
        f"--output /workspace/output/wpscan-{safe_domain}.txt 2>/dev/null"
    )
    return _exec_and_log("wpscan_scan", url, {}, cmd, timeout=LONG_TOOL_TIMEOUT)


def execute_code(language: str, code: str) -> dict[str, Any]:
    """Execute code in sandbox."""
    if language == "python":
        ext = "py"
    elif language == "node":
        ext = "js"
    else:
        return {"success": False, "data": {}, "error": f"Unsupported language: {language}"}

    # Use a unique heredoc delimiter to avoid collision with code content
    delimiter = f"HEREDOC_EOF_{secrets.token_hex(HEREDOC_TOKEN_BYTES)}"
    safe_lang = shlex.quote(language)
    runner = "python3" if language == "python" else language
    cmd = (
        f"cat > /tmp/exec_{safe_lang}.{ext} "
        f"<< '{delimiter}'\n{code}\n{delimiter}\n"
        f"cd /workspace && {runner} /tmp/exec_{safe_lang}.{ext}"
    )
    return _exec_and_log(
        "code_execute", language,
        {"language": language, "code_length": len(code)}, cmd
    )
