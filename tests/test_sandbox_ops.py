from unittest.mock import MagicMock, patch

from opspectre.core.sandbox_ops import sandbox_start, sandbox_status, sandbox_stop
from opspectre.sandbox.docker_runtime import SandboxError


class TestSandboxStart:
    def test_success(self):
        mock_rt = MagicMock()
        mock_rt.start.return_value = {
            "container_name": "opspectre-default",
            "container_id": "abc",
            "api_url": "http://127.0.0.1:48081",
        }
        with patch("opspectre.core.sandbox_ops.get_runtime", return_value=mock_rt):
            result = sandbox_start()
        assert result["success"] is True
        assert result["data"]["container_name"] == "opspectre-default"

    def test_failure(self):
        mock_rt = MagicMock()
        mock_rt.start.side_effect = SandboxError("docker not available")
        with patch("opspectre.core.sandbox_ops.get_runtime", return_value=mock_rt):
            result = sandbox_start()
        assert result["success"] is False
        assert "docker not available" in result["error"]


class TestSandboxStop:
    def test_success(self):
        mock_rt = MagicMock()
        mock_rt.stop.return_value = True
        with patch("opspectre.core.sandbox_ops.get_runtime", return_value=mock_rt), \
             patch("opspectre.core.sandbox_ops.reset_runtime"):
            result = sandbox_stop()
        assert result["success"] is True

    def test_not_running(self):
        mock_rt = MagicMock()
        mock_rt.stop.return_value = False
        with patch("opspectre.core.sandbox_ops.get_runtime", return_value=mock_rt):
            result = sandbox_stop()
        assert result["success"] is False
        assert "No sandbox" in result["error"]

    def test_error(self):
        mock_rt = MagicMock()
        mock_rt.stop.side_effect = SandboxError("removal failed")
        with patch("opspectre.core.sandbox_ops.get_runtime", return_value=mock_rt):
            result = sandbox_stop()
        assert result["success"] is False


class TestSandboxStatus:
    def test_running(self):
        mock_rt = MagicMock()
        mock_rt.status.return_value = "running"
        with patch("opspectre.core.sandbox_ops.get_runtime", return_value=mock_rt):
            result = sandbox_status()
        assert result["success"] is True
        assert result["data"]["status"] == "running"

    def test_stopped(self):
        mock_rt = MagicMock()
        mock_rt.status.return_value = "exited"
        with patch("opspectre.core.sandbox_ops.get_runtime", return_value=mock_rt):
            result = sandbox_status()
        assert result["success"] is True
        assert result["data"]["status"] == "exited"

    def test_none(self):
        mock_rt = MagicMock()
        mock_rt.status.return_value = None
        with patch("opspectre.core.sandbox_ops.get_runtime", return_value=mock_rt):
            result = sandbox_status()
        assert result["success"] is True
        assert result["data"]["status"] == "not_found"

    def test_error(self):
        mock_rt = MagicMock()
        mock_rt.status.side_effect = SandboxError("docker error")
        with patch("opspectre.core.sandbox_ops.get_runtime", return_value=mock_rt):
            result = sandbox_status()
        assert result["success"] is False
