"""Structured execution logging for OperationSpectre.

Every tool execution gets logged to a JSONL file on disk.
The agent can review logs before generating reports to identify
what failed, what's empty, what should be retried.
"""

import contextlib
import json
import logging
import threading
import time
from dataclasses import asdict, dataclass
from datetime import datetime, timezone

UTC = timezone.utc
from pathlib import Path
from typing import Any

_log = logging.getLogger("opspectre.execution_log")

# Default log location — lives alongside output
DEFAULT_LOG_DIR = Path("/workspace/output/logs")
LOG_FILE_NAME = "execution.jsonl"
SLOW_OPERATION_THRESHOLD_S = 60  # seconds
OUTPUT_SUMMARY_MAX_LINES = 3
OUTPUT_SUMMARY_MAX_CHARS = 120


@dataclass
class ExecutionEntry:
    """Single tool execution record."""
    tool: str                          # e.g. "nmap_scan", "nuclei_scan"
    target: str                        # primary target (host, domain, URL)
    params: dict[str, Any]             # all params passed
    started_at: str                    # ISO timestamp
    finished_at: str                   # ISO timestamp
    duration_s: float                  # wall clock seconds
    success: bool                      # exit code 0 or equivalent
    error: str | None = None           # error message if failed
    output_lines: int = 0              # line count of stdout
    output_bytes: int = 0              # byte count of stdout
    findings_summary: str = ""         # brief summary (e.g. "5 open ports", "3 CVEs found")
    exit_code: int = 0


class ExecutionLogger:
    """Persisted execution log — JSONL format for append-friendly writes."""

    def __init__(self, log_dir: Path | str | None = None):
        self.log_dir = Path(log_dir) if log_dir else DEFAULT_LOG_DIR
        self._dir_ready = False
        self.log_file = self.log_dir / LOG_FILE_NAME
        self._session_entries: list[ExecutionEntry] = []
        self._lock = threading.Lock()

    def _ensure_dir(self) -> None:
        """Lazily create the log directory on first write."""
        if not self._dir_ready:
            try:
                self.log_dir.mkdir(parents=True, exist_ok=True)
                self._dir_ready = True
            except OSError as e:
                _log.debug("Cannot create log directory %s: %s", self.log_dir, e)

    def log(self, entry: ExecutionEntry) -> None:
        """Append entry to JSONL file and in-memory session list."""
        self._ensure_dir()
        with self._lock:
            self._session_entries.append(entry)
            try:
                with open(self.log_file, "a", encoding="utf-8") as f:
                    f.write(json.dumps(asdict(entry), default=str) + "\n")
            except OSError as e:
                _log.debug("Failed to write execution log entry: %s", e)  # non-fatal

    def start(self, tool: str, target: str, params: dict[str, Any]) -> dict[str, Any]:
        """Return a context dict to pass to finish()."""
        return {
            "tool": tool,
            "target": target,
            "params": params,
            "started_at": datetime.now(UTC).isoformat(),
            "start_time": time.perf_counter(),
        }

    def finish(
        self,
        ctx: dict[str, Any],
        success: bool,
        stdout: str = "",
        stderr: str = "",
        error: str | None = None,
        exit_code: int = 0,
        findings_summary: str = "",
    ) -> ExecutionEntry:
        """Create and log the final entry."""
        now = time.perf_counter()
        entry = ExecutionEntry(
            tool=ctx["tool"],
            target=ctx["target"],
            params=ctx["params"],
            started_at=ctx["started_at"],
            finished_at=datetime.now(UTC).isoformat(),
            duration_s=round(now - ctx["start_time"], 2),
            success=success,
            error=error or (stderr[:500] if stderr and not success else None),
            output_lines=len(stdout.splitlines()) if stdout else 0,
            output_bytes=len(stdout.encode()) if stdout else 0,
            findings_summary=findings_summary,
            exit_code=exit_code,
        )
        self.log(entry)
        return entry

    def read_all(self, last_n: int | None = None) -> list[dict[str, Any]]:
        """Read log entries from disk. Returns last N if specified."""
        if not self.log_file.exists():
            return []
        entries = []
        try:
            with open(self.log_file, encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    if line:
                        entries.append(json.loads(line))
        except (json.JSONDecodeError, OSError) as e:
            _log.debug("Error reading execution log: %s", e)
        if last_n:
            return entries[-last_n:]
        return entries

    def read_session(self) -> list[ExecutionEntry]:
        """Return entries from current session only."""
        with self._lock:
            return list(self._session_entries)

    def clear(self) -> int:
        """Clear the log file. Returns number of entries removed."""
        count = len(self.read_all())
        with contextlib.suppress(OSError):
            self.log_file.unlink(missing_ok=True)
        with self._lock:
            self._session_entries.clear()
        return count


def summarize_output(tool: str, stdout: str) -> str:
    """Generate a brief findings summary based on tool type and output."""
    if not stdout or not stdout.strip():
        return "no output"

    lines = stdout.strip().splitlines()
    num_lines = len(lines)

    if tool in ("nmap_scan", "port_scan"):
        open_ports = sum(1 for ln in lines if "/tcp" in ln and "open" in ln)
        if open_ports:
            return f"{open_ports} open ports found"
        return f"{num_lines} lines, no open ports detected"

    if tool == "nuclei_scan":
        vuln_lines = [
            ln for ln in lines if "[" in ln and "]" in ln and any(
                kw in ln.lower()
                for kw in ("cve-", "vulnerability", "critical", "high", "medium")
            )
        ]
        if vuln_lines:
            return f"{len(vuln_lines)} potential findings"
        return f"{num_lines} lines, no findings"

    if tool == "subdomain_discovery":
        # Count unique domains found
        domains = set()
        for ln in lines:
            ln = ln.strip()
            if ln and "." in ln and " " not in ln:
                domains.add(ln)
        if domains:
            return f"{len(domains)} subdomains found"
        return f"{num_lines} lines, no subdomains parsed"

    if tool == "http_probe":
        status_codes = ("200", "301", "302", "403", "401")
        live = sum(1 for ln in lines if any(code in ln for code in status_codes))
        return f"{live} responsive targets out of {num_lines} lines"

    if tool == "osint_recon":
        return f"{num_lines} lines of OSINT data"

    if tool == "wpscan_scan":
        if "interesting finding" in stdout.lower() or "vulnerability" in stdout.lower():
            return "findings detected"
        return f"{num_lines} lines, no critical findings"

    # Generic
    if num_lines <= OUTPUT_SUMMARY_MAX_LINES:
        return f"{num_lines} lines: {stdout[:OUTPUT_SUMMARY_MAX_CHARS]}"
    return f"{num_lines} lines of output"


def _analyze_entry(entry: dict[str, Any]) -> dict[str, Any]:
    """Analyze a single execution log entry.

    Returns categorized results for one entry:
        {"failed": [], "empty_results": [], "slow_ops": [],
         "retry_suggestions": [], "is_success": bool}
    """
    tool = entry.get("tool", "unknown")
    target = entry.get("target", "")
    success = entry.get("success", False)
    output_lines = entry.get("output_lines", 0)
    output_bytes = entry.get("output_bytes", 0)
    duration = entry.get("duration_s", 0)
    error = entry.get("error")
    params = entry.get("params", {})
    summary = entry.get("findings_summary", "")

    result: dict[str, Any] = {
        "failed": [],
        "empty_results": [],
        "slow_ops": [],
        "retry_suggestions": [],
        "is_success": success,
    }

    if success:
        # Check for empty results
        if output_lines == 0 or output_bytes == 0:
            result["empty_results"].append({
                "tool": tool,
                "target": target,
                "suggestion": _empty_suggestion(tool, target, params),
            })
            result["retry_suggestions"].append({
                "tool": tool,
                "target": target,
                "reason": "Empty output \u2014 possible detection/timeout/incorrect target",
                "suggested_params": _retry_params(tool, params),
            })
        # Check for "no findings" even with output
        elif "no finding" in summary.lower() or "no open port" in summary.lower():
            result["retry_suggestions"].append({
                "tool": tool,
                "target": target,
                "reason": f"Ran successfully but {summary}",
                "suggested_params": _retry_params(tool, params),
            })
    else:
        result["failed"].append({
            "tool": tool,
            "target": target,
            "error": error or "Unknown error",
            "suggestion": _failure_suggestion(tool, error),
        })
        result["retry_suggestions"].append({
            "tool": tool,
            "target": target,
            "reason": f"Failed: {error}",
            "suggested_params": _retry_params(tool, params),
        })

    # Slow operations (>60s)
    if duration > SLOW_OPERATION_THRESHOLD_S:
        result["slow_ops"].append({
            "tool": tool,
            "target": target,
            "duration_s": duration,
        })

    return result


def _build_review_summary(
    total: int,
    succeeded: int,
    failed: list,
    empty_results: list,
    slow_ops: list,
    retry_suggestions: list,
) -> str:
    """Build a human-readable summary string from review counts."""
    summary_parts = [f"{total} tool executions: {succeeded} succeeded, {len(failed)} failed"]
    if empty_results:
        summary_parts.append(f"{len(empty_results)} returned empty results")
    if slow_ops:
        summary_parts.append(f"{len(slow_ops)} took over {SLOW_OPERATION_THRESHOLD_S}s")
    if retry_suggestions:
        summary_parts.append(f"{len(retry_suggestions)} retries suggested")
    return ". ".join(summary_parts) + "."


def review_run(entries: list[dict[str, Any]]) -> dict[str, Any]:
    """Analyze execution log and return actionable review.

    Returns:
        {
            "total": int,
            "succeeded": int,
            "failed": [{"tool", "target", "error", "suggestion"}],
            "empty_results": [{"tool", "target", "suggestion"}],
            "slow_operations": [{"tool", "target", "duration_s"}],
            "retry_suggestions": [{"tool", "target", "reason", "suggested_params"}],
            "summary": str
        }
    """
    if not entries:
        return {
            "total": 0,
            "succeeded": 0,
            "failed": [],
            "empty_results": [],
            "slow_operations": [],
            "retry_suggestions": [],
            "summary": "No execution log found. No tools have been run yet.",
        }

    failed: list[dict] = []
    empty_results: list[dict] = []
    slow_ops: list[dict] = []
    retry_suggestions: list[dict] = []
    succeeded = 0

    for entry in entries:
        analysis = _analyze_entry(entry)
        if analysis["is_success"]:
            succeeded += 1
        failed.extend(analysis["failed"])
        empty_results.extend(analysis["empty_results"])
        slow_ops.extend(analysis["slow_ops"])
        retry_suggestions.extend(analysis["retry_suggestions"])

    # Sort slow ops by duration desc
    slow_ops.sort(key=lambda x: x["duration_s"], reverse=True)

    return {
        "total": len(entries),
        "succeeded": succeeded,
        "failed": failed,
        "empty_results": empty_results,
        "slow_operations": slow_ops,
        "retry_suggestions": retry_suggestions,
        "summary": _build_review_summary(
            len(entries), succeeded, failed, empty_results, slow_ops, retry_suggestions
        ),
    }


def _empty_suggestion(tool: str, target: str, params: dict) -> str:
    suggestions = {
        "nmap_scan": "Try different port range or scan type. Target may be behind firewall.",
        "nuclei_scan": "Try broader severity or different template set. Target may not be HTTP.",
        "subdomain_discovery": (
            "Try alternative method (crt, full_passive). Domain may have wildcard DNS."
        ),
        "http_probe": "Target may be down or blocking requests. Try without rate limit.",
        "osint_recon": "Try full method if specific method returned nothing.",
        "gowitness_screenshots": "URLs may be unreachable. Verify targets with http_probe first.",
        "wpscan_scan": "May not be a WordPress site. Verify with http_probe tech detection.",
    }
    return suggestions.get(tool, "Verify target is correct and reachable.")


def _failure_suggestion(tool: str, error: str | None) -> str:
    if not error:
        return "Check sandbox status and retry."
    err_lower = error.lower()
    if "timeout" in err_lower:
        return "Increase timeout or reduce scan scope."
    if "not found" in err_lower or "no such" in err_lower:
        return "Tool may not be installed in sandbox. Check with sandbox_status."
    if "connection" in err_lower or "refused" in err_lower:
        return "Target may be unreachable. Verify network connectivity."
    if "permission" in err_lower or "denied" in err_lower:
        return "Permission issue. May need different scan technique."
    return f"Review error and retry: {error[:100]}"


def _retry_params(tool: str, params: dict) -> dict:
    """Suggest modified params for retry."""
    suggested = dict(params)

    if tool == "nmap_scan":
        if not params.get("stealth"):
            suggested["stealth"] = True
        if not params.get("ports"):
            suggested["ports"] = "80,443,8080,8443"

    elif tool == "nuclei_scan":
        current_sev = params.get("severity", "medium,high,critical")
        if current_sev != "low,medium,high,critical":
            suggested["severity"] = "low,medium,high,critical"

    elif tool == "subdomain_discovery":
        method = params.get("method", "subfinder")
        alt = {"subfinder": "crt", "crt": "full_passive", "full_passive": "subfinder"}
        suggested["method"] = alt.get(method, "full_passive")

    elif tool == "http_probe":
        if params.get("rate_limit", 5) > 1:
            suggested["rate_limit"] = 1

    return suggested


# Global execution logger instance
exec_logger = ExecutionLogger()
