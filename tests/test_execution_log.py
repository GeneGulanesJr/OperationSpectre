import json
from datetime import datetime

from opspectre.core.execution_log import (
    ExecutionEntry,
    ExecutionLogger,
    _analyze_entry,
    _build_review_summary,
    _empty_suggestion,
    _failure_suggestion,
    _retry_params,
    review_run,
    summarize_output,
)


class TestSummarizeOutput:
    def test_empty_string(self):
        assert summarize_output("nmap_scan", "") == "no output"

    def test_whitespace_only(self):
        assert summarize_output("nmap_scan", "   \n  ") == "no output"

    def test_nmap_open_ports(self):
        out = "80/tcp open http\n443/tcp open https\n"
        assert summarize_output("nmap_scan", out) == "2 open ports found"

    def test_nmap_no_open_ports(self):
        out = "Starting nmap...\nDone\n"
        assert summarize_output("nmap_scan", out) == "2 lines, no open ports detected"

    def test_port_scan_open_ports(self):
        out = "22/tcp open ssh\n"
        assert summarize_output("port_scan", out) == "1 open ports found"

    def test_nuclei_findings(self):
        out = "[CVE-2024-1234] [critical] vuln found\n[some-template] [high] issue\n"
        assert summarize_output("nuclei_scan", out) == "2 potential findings"

    def test_nuclei_no_findings(self):
        out = "scan completed\nno vulns\n"
        assert summarize_output("nuclei_scan", out) == "2 lines, no findings"

    def test_subdomain_discovery(self):
        out = "sub.example.com\napi.example.com\nwww.example.com\n"
        assert summarize_output("subdomain_discovery", out) == "3 subdomains found"

    def test_subdomain_discovery_no_results(self):
        out = "no subs found here\n"
        assert summarize_output("subdomain_discovery", out) == "1 lines, no subdomains parsed"

    def test_http_probe(self):
        out = "http://example.com 200\nhttp://test.com 403\nhttp://gone.com 500\n"
        assert summarize_output("http_probe", out) == "2 responsive targets out of 3 lines"

    def test_osint_recon(self):
        out = "line1\nline2\nline3\n"
        assert summarize_output("osint_recon", out) == "3 lines of OSINT data"

    def test_wpscan_findings(self):
        out = "Interesting Finding: ...\nVulnerability: ...\n"
        assert summarize_output("wpscan_scan", out) == "findings detected"

    def test_wpscan_no_findings(self):
        out = "scan finished\nno issues\n"
        assert summarize_output("wpscan_scan", out) == "2 lines, no critical findings"

    def test_generic_short_output(self):
        out = "hello"
        assert summarize_output("unknown_tool", out) == "1 lines: hello"

    def test_generic_long_output(self):
        lines = [f"line {i}" for i in range(10)]
        out = "\n".join(lines)
        assert summarize_output("unknown_tool", out) == "10 lines of output"


class TestAnalyzeEntry:
    def _make_entry(self, **overrides):
        defaults = {
            "tool": "nmap_scan",
            "target": "192.168.1.1",
            "params": {},
            "started_at": "2025-01-01T00:00:00",
            "finished_at": "2025-01-01T00:01:00",
            "duration_s": 60,
            "success": True,
            "output_lines": 10,
            "output_bytes": 500,
            "findings_summary": "2 open ports found",
            "exit_code": 0,
        }
        defaults.update(overrides)
        return defaults

    def test_success_with_output(self):
        entry = self._make_entry()
        result = _analyze_entry(entry)
        assert result["is_success"] is True
        assert result["failed"] == []
        assert result["empty_results"] == []
        assert result["retry_suggestions"] == []

    def test_success_empty_output(self):
        entry = self._make_entry(output_lines=0, output_bytes=0)
        result = _analyze_entry(entry)
        assert result["is_success"] is True
        assert len(result["empty_results"]) == 1
        assert result["empty_results"][0]["tool"] == "nmap_scan"
        assert len(result["retry_suggestions"]) == 1

    def test_success_no_findings_summary(self):
        entry = self._make_entry(findings_summary="no open ports detected")
        result = _analyze_entry(entry)
        assert len(result["retry_suggestions"]) == 1
        assert "no open port" in result["retry_suggestions"][0]["reason"].lower()

    def test_failed_entry(self):
        entry = self._make_entry(success=False, error="Connection refused")
        result = _analyze_entry(entry)
        assert result["is_success"] is False
        assert len(result["failed"]) == 1
        assert result["failed"][0]["error"] == "Connection refused"
        assert len(result["retry_suggestions"]) == 1

    def test_slow_operation(self):
        entry = self._make_entry(duration_s=120)
        result = _analyze_entry(entry)
        assert len(result["slow_ops"]) == 1
        assert result["slow_ops"][0]["duration_s"] == 120

    def test_fast_operation_no_slow(self):
        entry = self._make_entry(duration_s=30)
        result = _analyze_entry(entry)
        assert result["slow_ops"] == []


class TestReviewRun:
    def test_empty_entries(self):
        result = review_run([])
        assert result["total"] == 0
        assert result["succeeded"] == 0
        assert result["summary"] == "No execution log found. No tools have been run yet."

    def test_mixed_entries(self):
        entries = [
            {"tool": "nmap_scan", "target": "a", "success": True,
             "output_lines": 5, "output_bytes": 100, "duration_s": 10,
             "error": None, "params": {}, "findings_summary": "ok"},
            {"tool": "nuclei_scan", "target": "b", "success": False,
             "output_lines": 0, "output_bytes": 0, "duration_s": 5,
             "error": "timeout", "params": {}, "findings_summary": ""},
            {"tool": "subdomain_discovery", "target": "c", "success": True,
             "output_lines": 0, "output_bytes": 0, "duration_s": 3,
             "error": None, "params": {"method": "subfinder"}, "findings_summary": ""},
        ]
        result = review_run(entries)
        assert result["total"] == 3
        assert result["succeeded"] == 2
        assert len(result["failed"]) == 1
        assert len(result["empty_results"]) == 1
        assert len(result["retry_suggestions"]) == 2


class TestBuildReviewSummary:
    def test_basic(self):
        s = _build_review_summary(5, 3, [{"tool": "x"}], [], [], [])
        assert "5 tool executions" in s
        assert "3 succeeded" in s
        assert "1 failed" in s

    def test_with_extras(self):
        s = _build_review_summary(
            10, 7,
            [{"tool": "a"}],
            [{"tool": "b"}],
            [{"tool": "c", "duration_s": 90}],
            [{"tool": "d"}],
        )
        assert "1 returned empty results" in s
        assert "1 took over 60s" in s
        assert "1 retries suggested" in s


class TestEmptySuggestion:
    def test_known_tool(self):
        s = _empty_suggestion("nmap_scan", "target", {})
        assert "firewall" in s.lower() or "port" in s.lower()

    def test_unknown_tool(self):
        s = _empty_suggestion("custom_tool", "target", {})
        assert "Verify target" in s


class TestFailureSuggestion:
    def test_none_error(self):
        assert "sandbox" in _failure_suggestion("tool", None).lower() or "retry" in _failure_suggestion("tool", None).lower()

    def test_timeout_error(self):
        assert "timeout" in _failure_suggestion("tool", "Operation timeout after 30s").lower()

    def test_not_found_error(self):
        assert "installed" in _failure_suggestion("tool", "nmap not found").lower()

    def test_connection_error(self):
        assert "unreachable" in _failure_suggestion("tool", "Connection refused").lower()

    def test_permission_error(self):
        assert "permission" in _failure_suggestion("tool", "Permission denied").lower()

    def test_generic_error(self):
        result = _failure_suggestion("tool", "Some unknown error")
        assert "Some unknown error" in result


class TestRetryParams:
    def test_nmap_adds_stealth(self):
        result = _retry_params("nmap_scan", {"stealth": False})
        assert result["stealth"] is True
        assert "ports" in result

    def test_nuclei_widens_severity(self):
        result = _retry_params("nuclei_scan", {"severity": "high,critical"})
        assert result["severity"] == "low,medium,high,critical"

    def test_subdomain_cycles_method(self):
        result = _retry_params("subdomain_discovery", {"method": "subfinder"})
        assert result["method"] == "crt"

    def test_subdomain_full_passive_cycle(self):
        result = _retry_params("subdomain_discovery", {"method": "full_passive"})
        assert result["method"] == "subfinder"

    def test_http_probe_reduces_rate(self):
        result = _retry_params("http_probe", {"rate_limit": 5})
        assert result["rate_limit"] == 1

    def test_unknown_tool_returns_copy(self):
        original = {"foo": "bar"}
        result = _retry_params("unknown_tool", original)
        assert result == original
        assert result is not original


class TestExecutionLogger:
    def test_log_and_read(self, tmp_path):
        logger = ExecutionLogger(log_dir=tmp_path)
        entry = ExecutionEntry(
            tool="nmap_scan", target="10.0.0.1", params={},
            started_at="2025-01-01T00:00:00", finished_at="2025-01-01T00:01:00",
            duration_s=60.0, success=True,
        )
        logger.log(entry)
        entries = logger.read_all()
        assert len(entries) == 1
        assert entries[0]["tool"] == "nmap_scan"
        assert entries[0]["target"] == "10.0.0.1"

    def test_read_last_n(self, tmp_path):
        logger = ExecutionLogger(log_dir=tmp_path)
        for i in range(5):
            entry = ExecutionEntry(
                tool=f"tool_{i}", target=f"target_{i}", params={},
                started_at="2025-01-01T00:00:00", finished_at="2025-01-01T00:01:00",
                duration_s=1.0, success=True,
            )
            logger.log(entry)
        entries = logger.read_all(last_n=2)
        assert len(entries) == 2
        assert entries[0]["tool"] == "tool_3"
        assert entries[1]["tool"] == "tool_4"

    def test_read_session(self, tmp_path):
        logger = ExecutionLogger(log_dir=tmp_path)
        entry = ExecutionEntry(
            tool="test", target="t", params={},
            started_at="2025-01-01T00:00:00", finished_at="2025-01-01T00:01:00",
            duration_s=1.0, success=True,
        )
        logger.log(entry)
        session = logger.read_session()
        assert len(session) == 1
        assert session[0].tool == "test"

    def test_clear(self, tmp_path):
        logger = ExecutionLogger(log_dir=tmp_path)
        entry = ExecutionEntry(
            tool="test", target="t", params={},
            started_at="2025-01-01T00:00:00", finished_at="2025-01-01T00:01:00",
            duration_s=1.0, success=True,
        )
        logger.log(entry)
        count = logger.clear()
        assert count == 1
        assert logger.read_all() == []

    def test_read_nonexistent(self, tmp_path):
        logger = ExecutionLogger(log_dir=tmp_path / "nonexistent")
        assert logger.read_all() == []

    def test_start_finish_roundtrip(self, tmp_path):
        logger = ExecutionLogger(log_dir=tmp_path)
        ctx = logger.start("nmap_scan", "10.0.0.1", {"ports": "80"})
        entry = logger.finish(ctx, success=True, stdout="80/tcp open", exit_code=0)
        assert entry.tool == "nmap_scan"
        assert entry.target == "10.0.0.1"
        assert entry.success is True
        assert entry.output_lines == 1
        entries = logger.read_all()
        assert len(entries) == 1
