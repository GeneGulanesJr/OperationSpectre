import os
from unittest.mock import MagicMock, patch, PropertyMock

import pytest

from opspectre.sandbox.docker_runtime import DockerRuntime, SandboxError


class TestResolveDockerHost:
    def test_default_localhost(self, monkeypatch):
        monkeypatch.delenv("DOCKER_HOST", raising=False)
        runtime = object.__new__(DockerRuntime)
        assert runtime._resolve_docker_host() == "127.0.0.1"

    def test_tcp_url(self, monkeypatch):
        monkeypatch.setenv("DOCKER_HOST", "tcp://192.168.99.100:2376")
        runtime = object.__new__(DockerRuntime)
        assert runtime._resolve_docker_host() == "192.168.99.100"

    def test_http_url(self, monkeypatch):
        monkeypatch.setenv("DOCKER_HOST", "http://10.0.0.1:2375")
        runtime = object.__new__(DockerRuntime)
        assert runtime._resolve_docker_host() == "10.0.0.1"

    def test_https_url(self, monkeypatch):
        monkeypatch.setenv("DOCKER_HOST", "https://my-docker.host:2376")
        runtime = object.__new__(DockerRuntime)
        assert runtime._resolve_docker_host() == "my-docker.host"

    def test_unix_socket_fallback(self, monkeypatch):
        monkeypatch.setenv("DOCKER_HOST", "unix:///var/run/docker.sock")
        runtime = object.__new__(DockerRuntime)
        assert runtime._resolve_docker_host() == "127.0.0.1"


class TestIsConnected:
    def test_connected(self):
        runtime = object.__new__(DockerRuntime)
        runtime._container = MagicMock()
        runtime._tool_server_port = 48081
        assert runtime.is_connected() is True

    def test_no_container(self):
        runtime = object.__new__(DockerRuntime)
        runtime._container = None
        runtime._tool_server_port = 48081
        assert runtime.is_connected() is False

    def test_no_port(self):
        runtime = object.__new__(DockerRuntime)
        runtime._container = MagicMock()
        runtime._tool_server_port = None
        assert runtime.is_connected() is False


class TestGetSandboxInfo:
    def test_with_container(self):
        runtime = object.__new__(DockerRuntime)
        mock_container = MagicMock()
        mock_container.id = "abc123"
        runtime._container = mock_container
        runtime._tool_server_port = 48081
        runtime._tool_server_token = "tok123"
        with patch.object(runtime, "_resolve_docker_host", return_value="127.0.0.1"):
            info = runtime.get_sandbox_info()
        assert info["container_id"] == "abc123"
        assert "127.0.0.1" in info["api_url"]
        assert info["auth_token"] == "tok123"

    def test_no_container(self):
        runtime = object.__new__(DockerRuntime)
        runtime._container = None
        assert runtime.get_sandbox_info() == {}


class TestRequireDocker:
    def test_docker_available(self):
        import opspectre.sandbox.docker_runtime as mod
        if mod._HAS_DOCKER:
            result = mod._require_docker()
            assert result is not None

    def test_docker_not_available(self):
        import opspectre.sandbox.docker_runtime as mod
        original = mod._docker_mod
        mod._docker_mod = None
        try:
            with pytest.raises(SandboxError, match="required"):
                mod._require_docker()
        finally:
            mod._docker_mod = original


class TestRequireHttpx:
    def test_httpx_available(self):
        import opspectre.sandbox.docker_runtime as mod
        if mod._httpx_mod is not None:
            result = mod._require_httpx()
            assert result is not None

    def test_httpx_not_available(self):
        import opspectre.sandbox.docker_runtime as mod
        original = mod._httpx_mod
        mod._httpx_mod = None
        try:
            with pytest.raises(SandboxError, match="required"):
                mod._require_httpx()
        finally:
            mod._httpx_mod = original


class TestApiPost:
    def test_raises_when_no_sandbox(self):
        runtime = object.__new__(DockerRuntime)
        runtime._tool_server_port = None
        runtime._tool_server_token = None
        with pytest.raises(SandboxError, match="No sandbox running"):
            runtime._api_post("/execute", {})


class TestSandboxError:
    def test_message_and_details(self):
        err = SandboxError("test msg", "detail info")
        assert err.message == "test msg"
        assert err.details == "detail info"
        assert str(err) == "test msg"

    def test_no_details(self):
        err = SandboxError("msg")
        assert err.details is None
