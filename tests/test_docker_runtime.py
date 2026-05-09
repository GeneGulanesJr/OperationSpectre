import os
from unittest.mock import MagicMock, patch

import pytest

from opspectre.sandbox.docker_runtime import DockerRuntime, SandboxError


class TestResolveDockerHost:
    def test_default_localhost(self, monkeypatch):
        monkeypatch.delenv("DOCKER_HOST", raising=False)
        rt = object.__new__(DockerRuntime)
        assert rt._resolve_docker_host() == "127.0.0.1"

    def test_tcp_url(self, monkeypatch):
        monkeypatch.setenv("DOCKER_HOST", "tcp://192.168.99.100:2376")
        rt = object.__new__(DockerRuntime)
        assert rt._resolve_docker_host() == "192.168.99.100"

    def test_http_url(self, monkeypatch):
        monkeypatch.setenv("DOCKER_HOST", "http://10.0.0.1:2375")
        rt = object.__new__(DockerRuntime)
        assert rt._resolve_docker_host() == "10.0.0.1"

    def test_https_url(self, monkeypatch):
        monkeypatch.setenv("DOCKER_HOST", "https://my-docker.host:2376")
        rt = object.__new__(DockerRuntime)
        assert rt._resolve_docker_host() == "my-docker.host"

    def test_unix_socket_fallback(self, monkeypatch):
        monkeypatch.setenv("DOCKER_HOST", "unix:///var/run/docker.sock")
        rt = object.__new__(DockerRuntime)
        assert rt._resolve_docker_host() == "127.0.0.1"

    def test_empty_string(self, monkeypatch):
        monkeypatch.setenv("DOCKER_HOST", "")
        rt = object.__new__(DockerRuntime)
        assert rt._resolve_docker_host() == "127.0.0.1"

    def test_tcp_without_port(self, monkeypatch):
        monkeypatch.setenv("DOCKER_HOST", "tcp://myhost")
        rt = object.__new__(DockerRuntime)
        assert rt._resolve_docker_host() == "myhost"


class TestApiPostValidation:
    def test_raises_when_no_port(self):
        rt = object.__new__(DockerRuntime)
        rt._tool_server_port = None
        rt._tool_server_token = "tok"
        with pytest.raises(SandboxError, match="No sandbox running"):
            rt._api_post("/execute", {})

    def test_raises_when_no_token(self):
        rt = object.__new__(DockerRuntime)
        rt._tool_server_port = 48081
        rt._tool_server_token = None
        with pytest.raises(SandboxError, match="No sandbox running"):
            rt._api_post("/execute", {})

    def test_raises_when_both_none(self):
        rt = object.__new__(DockerRuntime)
        rt._tool_server_port = None
        rt._tool_server_token = None
        with pytest.raises(SandboxError, match="No sandbox running"):
            rt._api_post("/execute", {})


class TestGetSandboxInfoContract:
    def test_returns_dict_with_expected_keys(self):
        rt = object.__new__(DockerRuntime)
        mock_container = MagicMock()
        mock_container.id = "abc123"
        rt._container = mock_container
        rt._tool_server_port = 48081
        rt._tool_server_token = "tok123"
        with patch.object(rt, "_resolve_docker_host", return_value="127.0.0.1"):
            info = rt.get_sandbox_info()
        assert "container_id" in info
        assert "api_url" in info
        assert "auth_token" in info
        assert info["container_id"] == "abc123"
        assert ":48081" in info["api_url"]
        assert info["auth_token"] == "tok123"

    def test_returns_empty_when_no_container(self):
        rt = object.__new__(DockerRuntime)
        rt._container = None
        assert rt.get_sandbox_info() == {}


class TestExecuteResultShaping:
    def test_shapes_success_response(self):
        rt = object.__new__(DockerRuntime)
        rt._tool_server_port = 48081
        rt._tool_server_token = "tok"
        with patch.object(rt, "_api_post", return_value={
            "stdout": "hello", "stderr": "", "exit_code": 0
        }):
            result = rt.execute("echo hello")
        assert result["stdout"] == "hello"
        assert result["stderr"] == ""
        assert result["exit_code"] == 0

    def test_shapes_error_response(self):
        rt = object.__new__(DockerRuntime)
        rt._tool_server_port = 48081
        rt._tool_server_token = "tok"
        with patch.object(rt, "_api_post", return_value={
            "error": "command timed out"
        }):
            result = rt.execute("slow_cmd")
        assert result["stdout"] == ""
        assert "timed out" in result["stderr"]
        assert result["exit_code"] == -1

    def test_passes_timeout_from_config(self, monkeypatch):
        monkeypatch.setenv("OPSPECTRE_TIMEOUT", "30")
        rt = object.__new__(DockerRuntime)
        rt._tool_server_port = 48081
        rt._tool_server_token = "tok"
        with patch.object(rt, "_api_post", return_value={
            "stdout": "", "stderr": "", "exit_code": 0
        }) as mock_post:
            rt.execute("cmd")
        call_args = mock_post.call_args
        assert call_args[0][1]["timeout"] == 30

    def test_custom_timeout_overrides_config(self, monkeypatch):
        monkeypatch.setenv("OPSPECTRE_TIMEOUT", "30")
        rt = object.__new__(DockerRuntime)
        rt._tool_server_port = 48081
        rt._tool_server_token = "tok"
        with patch.object(rt, "_api_post", return_value={
            "stdout": "", "stderr": "", "exit_code": 0
        }) as mock_post:
            rt.execute("cmd", timeout=60)
        call_args = mock_post.call_args
        assert call_args[1].get("timeout") == 60


class TestStopCleanup:
    def test_clears_state_on_success(self):
        rt = object.__new__(DockerRuntime)
        rt._tool_server_port = 48081
        rt._tool_server_token = "tok"
        rt._container = MagicMock()
        mock_client = MagicMock()
        mock_container = MagicMock()
        mock_client.containers.get.return_value = mock_container
        rt.client = mock_client
        result = rt.stop()
        assert result is True
        assert rt._container is None
        assert rt._tool_server_port is None
        assert rt._tool_server_token is None

    def test_returns_false_on_not_found(self):
        import opspectre.sandbox.docker_runtime as mod
        rt = object.__new__(DockerRuntime)
        rt._tool_server_port = 48081
        rt._tool_server_token = "tok"
        rt._container = MagicMock()
        mock_client = MagicMock()
        mock_client.containers.get.side_effect = mod.NotFound("not found")
        rt.client = mock_client
        result = rt.stop()
        assert result is False


class TestSandboxError:
    def test_carries_message_and_details(self):
        err = SandboxError("msg", "detail")
        assert err.message == "msg"
        assert err.details == "detail"
        assert str(err) == "msg"

    def test_details_defaults_to_none(self):
        err = SandboxError("msg")
        assert err.details is None

    def test_is_exception(self):
        with pytest.raises(SandboxError, match="boom"):
            raise SandboxError("boom")
