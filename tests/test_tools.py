from unittest.mock import MagicMock, patch

from opspectre.core.tools import (
    discover_subdomains,
    execute_code,
    execute_shell,
    osint_recon,
    port_scan,
    probe_http,
    run_nmap_scan,
    scan_nuclei,
    wpscan_scan,
)
from opspectre.sandbox.docker_runtime import SandboxError


def _mock_runtime_and_logger():
    mock_rt = MagicMock()
    mock_rt.execute.return_value = {"stdout": "output", "stderr": "", "exit_code": 0}
    mock_logger = MagicMock()
    mock_logger.start.return_value = {"tool": "t", "target": "x", "params": {}, "started_at": "", "start_time": 0}
    return mock_rt, mock_logger


class TestRunNmapScan:
    def test_basic_scan(self):
        mock_rt, mock_logger = _mock_runtime_and_logger()
        with patch("opspectre.core.tools.get_runtime", return_value=mock_rt), \
             patch("opspectre.core.tools.exec_logger", mock_logger):
            result = run_nmap_scan("192.168.1.1")
        assert result["success"] is True
        cmd = mock_rt.execute.call_args[0][0]
        assert "nmap" in cmd
        assert "192.168.1.1" in cmd

    def test_with_ports(self):
        mock_rt, mock_logger = _mock_runtime_and_logger()
        with patch("opspectre.core.tools.get_runtime", return_value=mock_rt), \
             patch("opspectre.core.tools.exec_logger", mock_logger):
            result = run_nmap_scan("10.0.0.1", ports="80,443")
        cmd = mock_rt.execute.call_args[0][0]
        assert "-p" in cmd
        assert "80,443" in cmd

    def test_stealth_mode(self):
        mock_rt, mock_logger = _mock_runtime_and_logger()
        with patch("opspectre.core.tools.get_runtime", return_value=mock_rt), \
             patch("opspectre.core.tools.exec_logger", mock_logger):
            run_nmap_scan("10.0.0.1", stealth=True)
        cmd = mock_rt.execute.call_args[0][0]
        assert "-T2" in cmd

    def test_failure(self):
        mock_rt, mock_logger = _mock_runtime_and_logger()
        mock_rt.execute.return_value = {"stdout": "", "stderr": "error", "exit_code": 1}
        with patch("opspectre.core.tools.get_runtime", return_value=mock_rt), \
             patch("opspectre.core.tools.exec_logger", mock_logger):
            result = run_nmap_scan("10.0.0.1")
        assert result["success"] is False


class TestDiscoverSubdomains:
    def test_subfinder(self):
        mock_rt, mock_logger = _mock_runtime_and_logger()
        with patch("opspectre.core.tools.get_runtime", return_value=mock_rt), \
             patch("opspectre.core.tools.exec_logger", mock_logger):
            discover_subdomains("example.com", method="subfinder")
        cmd = mock_rt.execute.call_args[0][0]
        assert "subfinder" in cmd
        assert "example.com" in cmd

    def test_crt_method(self):
        mock_rt, mock_logger = _mock_runtime_and_logger()
        with patch("opspectre.core.tools.get_runtime", return_value=mock_rt), \
             patch("opspectre.core.tools.exec_logger", mock_logger):
            discover_subdomains("example.com", method="crt")
        cmd = mock_rt.execute.call_args[0][0]
        assert "osint_ct_subdomains" in cmd


class TestProbeHttp:
    def test_single_target(self):
        mock_rt, mock_logger = _mock_runtime_and_logger()
        with patch("opspectre.core.tools.get_runtime", return_value=mock_rt), \
             patch("opspectre.core.tools.exec_logger", mock_logger):
            probe_http("http://example.com")
        cmd = mock_rt.execute.call_args[0][0]
        assert "httpx" in cmd

    def test_list_targets(self):
        mock_rt, mock_logger = _mock_runtime_and_logger()
        with patch("opspectre.core.tools.get_runtime", return_value=mock_rt), \
             patch("opspectre.core.tools.exec_logger", mock_logger):
            probe_http(["http://a.com", "http://b.com"])
        cmd = mock_rt.execute.call_args[0][0]
        assert "echo" in cmd
        assert "httpx" in cmd


class TestScanNuclei:
    def test_single_target(self):
        mock_rt, mock_logger = _mock_runtime_and_logger()
        with patch("opspectre.core.tools.get_runtime", return_value=mock_rt), \
             patch("opspectre.core.tools.exec_logger", mock_logger):
            scan_nuclei("http://example.com")
        cmd = mock_rt.execute.call_args[0][0]
        assert "nuclei" in cmd
        assert "-u" in cmd

    def test_list_targets(self):
        mock_rt, mock_logger = _mock_runtime_and_logger()
        with patch("opspectre.core.tools.get_runtime", return_value=mock_rt), \
             patch("opspectre.core.tools.exec_logger", mock_logger):
            scan_nuclei(["http://a.com", "http://b.com"])
        cmd = mock_rt.execute.call_args[0][0]
        assert "nuclei" in cmd
        assert "-l" in cmd


class TestOsintRecon:
    def test_full_method(self):
        mock_rt, mock_logger = _mock_runtime_and_logger()
        with patch("opspectre.core.tools.get_runtime", return_value=mock_rt), \
             patch("opspectre.core.tools.exec_logger", mock_logger):
            osint_recon("example.com", method="full")
        cmd = mock_rt.execute.call_args[0][0]
        assert "osint_full_passive" in cmd

    def test_shodan_method(self):
        mock_rt, mock_logger = _mock_runtime_and_logger()
        with patch("opspectre.core.tools.get_runtime", return_value=mock_rt), \
             patch("opspectre.core.tools.exec_logger", mock_logger):
            osint_recon("example.com", method="shodan")
        cmd = mock_rt.execute.call_args[0][0]
        assert "osint_shodan" in cmd


class TestPortScan:
    def test_quick_profile(self):
        mock_rt, mock_logger = _mock_runtime_and_logger()
        with patch("opspectre.core.tools.get_runtime", return_value=mock_rt), \
             patch("opspectre.core.tools.exec_logger", mock_logger):
            port_scan("10.0.0.1", scan_type="quick")
        cmd = mock_rt.execute.call_args[0][0]
        assert "-F" in cmd

    def test_stealth_profile(self):
        mock_rt, mock_logger = _mock_runtime_and_logger()
        with patch("opspectre.core.tools.get_runtime", return_value=mock_rt), \
             patch("opspectre.core.tools.exec_logger", mock_logger):
            port_scan("10.0.0.1", scan_type="stealth")
        cmd = mock_rt.execute.call_args[0][0]
        assert "stealth_nmap" in cmd


class TestWpscanScan:
    def test_basic_scan(self):
        mock_rt, mock_logger = _mock_runtime_and_logger()
        with patch("opspectre.core.tools.get_runtime", return_value=mock_rt), \
             patch("opspectre.core.tools.exec_logger", mock_logger):
            wpscan_scan("http://wp.example.com")
        cmd = mock_rt.execute.call_args[0][0]
        assert "wpscan" in cmd
        assert "--url" in cmd


class TestExecuteCode:
    def test_python(self):
        mock_rt, mock_logger = _mock_runtime_and_logger()
        with patch("opspectre.core.tools.get_runtime", return_value=mock_rt), \
             patch("opspectre.core.tools.exec_logger", mock_logger):
            result = execute_code("python", "print('hi')")
        assert result["success"] is True
        cmd = mock_rt.execute.call_args[0][0]
        assert "python3" in cmd

    def test_node(self):
        mock_rt, mock_logger = _mock_runtime_and_logger()
        with patch("opspectre.core.tools.get_runtime", return_value=mock_rt), \
             patch("opspectre.core.tools.exec_logger", mock_logger):
            result = execute_code("node", "console.log('hi')")
        cmd = mock_rt.execute.call_args[0][0]
        assert "node" in cmd

    def test_unsupported_language(self):
        mock_rt, mock_logger = _mock_runtime_and_logger()
        with patch("opspectre.core.tools.get_runtime", return_value=mock_rt), \
             patch("opspectre.core.tools.exec_logger", mock_logger):
            result = execute_code("rust", "fn main() {}")
        assert result["success"] is False
        assert "Unsupported" in result["error"]


class TestExecuteShell:
    def test_basic(self):
        mock_rt, mock_logger = _mock_runtime_and_logger()
        with patch("opspectre.core.tools.get_runtime", return_value=mock_rt), \
             patch("opspectre.core.tools.exec_logger", mock_logger):
            result = execute_shell("whoami")
        assert result["success"] is True

    def test_sandbox_error(self):
        mock_rt, mock_logger = _mock_runtime_and_logger()
        mock_rt.execute.side_effect = SandboxError("down")
        with patch("opspectre.core.tools.get_runtime", return_value=mock_rt), \
             patch("opspectre.core.tools.exec_logger", mock_logger):
            result = execute_shell("whoami")
        assert result["success"] is False
