import sys
from unittest.mock import MagicMock, patch

import pytest

from opspectre.core.sandbox_ops import sandbox_start, sandbox_status, sandbox_stop
from opspectre.sandbox.docker_runtime import SandboxError


class TestSandboxStartResponseContract:
    def test_extracts_container_fields(self):
        mock_rt = MagicMock()
        mock_rt.start.return_value = {
            "container_name": "opspectre-default",
            "container_id": "abc123def",
            "api_url": "http://127.0.0.1:48081",
            "auth_token": "tok_abc",
        }
        with patch("opspectre.core.sandbox_ops.get_runtime", return_value=mock_rt):
            result = sandbox_start()
        assert result["success"] is True
        assert result["data"]["container_name"] == "opspectre-default"
        assert result["data"]["container_id"] == "abc123def"
        assert result["data"]["api_url"] == "http://127.0.0.1:48081"
        assert result["error"] is None

    def test_extracts_partial_fields(self):
        mock_rt = MagicMock()
        mock_rt.start.return_value = {"container_name": "opspectre-default"}
        with patch("opspectre.core.sandbox_ops.get_runtime", return_value=mock_rt):
            result = sandbox_start()
        assert result["success"] is True
        assert result["data"]["container_name"] == "opspectre-default"
        assert result["data"]["container_id"] is None
        assert result["data"]["api_url"] is None

    def test_wraps_sandbox_error_message(self):
        mock_rt = MagicMock()
        mock_rt.start.side_effect = SandboxError("Docker not available", "Install Docker first")
        with patch("opspectre.core.sandbox_ops.get_runtime", return_value=mock_rt):
            result = sandbox_start()
        assert result["success"] is False
        assert result["data"] == {}
        assert result["error"] == "Docker not available"

    def test_propagates_non_sandbox_exceptions(self):
        mock_rt = MagicMock()
        mock_rt.start.side_effect = RuntimeError("unexpected")
        with patch("opspectre.core.sandbox_ops.get_runtime", return_value=mock_rt):
            with pytest.raises(RuntimeError, match="unexpected"):
                sandbox_start()


class TestSandboxStopBranching:
    def test_calls_reset_runtime_on_success(self):
        mock_rt = MagicMock()
        mock_rt.stop.return_value = True
        with patch("opspectre.core.sandbox_ops.get_runtime", return_value=mock_rt), \
             patch("opspectre.core.sandbox_ops.reset_runtime") as mock_reset:
            result = sandbox_stop()
        assert result["success"] is True
        assert result["data"]["status"] == "stopped"
        mock_reset.assert_called_once()

    def test_reset_called_even_when_not_running(self):
        mock_rt = MagicMock()
        mock_rt.stop.return_value = False
        with patch("opspectre.core.sandbox_ops.get_runtime", return_value=mock_rt), \
             patch("opspectre.core.sandbox_ops.reset_runtime") as mock_reset:
            result = sandbox_stop()
        assert result["success"] is False
        assert "No sandbox" in result["error"]
        mock_reset.assert_called_once()

    def test_error_path_no_reset(self):
        mock_rt = MagicMock()
        mock_rt.stop.side_effect = SandboxError("removal failed")
        with patch("opspectre.core.sandbox_ops.get_runtime", return_value=mock_rt), \
             patch("opspectre.core.sandbox_ops.reset_runtime") as mock_reset:
            result = sandbox_stop()
        assert result["success"] is False
        mock_reset.assert_not_called()


class TestSandboxStatusFallback:
    def test_running_status(self):
        mock_rt = MagicMock()
        mock_rt.status.return_value = "running"
        with patch("opspectre.core.sandbox_ops.get_runtime", return_value=mock_rt):
            result = sandbox_status()
        assert result["data"]["status"] == "running"

    def test_exited_status(self):
        mock_rt = MagicMock()
        mock_rt.status.return_value = "exited"
        with patch("opspectre.core.sandbox_ops.get_runtime", return_value=mock_rt):
            result = sandbox_status()
        assert result["data"]["status"] == "exited"

    def test_none_falls_back_to_not_found(self):
        mock_rt = MagicMock()
        mock_rt.status.return_value = None
        with patch("opspectre.core.sandbox_ops.get_runtime", return_value=mock_rt):
            result = sandbox_status()
        assert result["data"]["status"] == "not_found"

    def test_empty_string_falls_back_to_not_found(self):
        mock_rt = MagicMock()
        mock_rt.status.return_value = ""
        with patch("opspectre.core.sandbox_ops.get_runtime", return_value=mock_rt):
            result = sandbox_status()
        assert result["data"]["status"] == "not_found"

    def test_error_returns_failure(self):
        mock_rt = MagicMock()
        mock_rt.status.side_effect = SandboxError("docker error")
        with patch("opspectre.core.sandbox_ops.get_runtime", return_value=mock_rt):
            result = sandbox_status()
        assert result["success"] is False
        assert "docker error" in result["error"]


class TestResponseShape:
    def test_start_has_required_keys(self):
        mock_rt = MagicMock()
        mock_rt.start.return_value = {"container_name": "x", "container_id": "y", "api_url": "z"}
        with patch("opspectre.core.sandbox_ops.get_runtime", return_value=mock_rt):
            result = sandbox_start()
        for key in ("success", "data", "error"):
            assert key in result

    def test_stop_has_required_keys(self):
        mock_rt = MagicMock()
        mock_rt.stop.return_value = True
        with patch("opspectre.core.sandbox_ops.get_runtime", return_value=mock_rt), \
             patch("opspectre.core.sandbox_ops.reset_runtime"):
            result = sandbox_stop()
        for key in ("success", "data", "error"):
            assert key in result

    def test_status_has_required_keys(self):
        mock_rt = MagicMock()
        mock_rt.status.return_value = "running"
        with patch("opspectre.core.sandbox_ops.get_runtime", return_value=mock_rt):
            result = sandbox_status()
        for key in ("success", "data", "error"):
            assert key in result
