import os
import sys
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest


def _import_tool_server(monkeypatch, token="test-token", port=9100):
    monkeypatch.setenv("OPSPECTRE_SANDBOX_MODE", "true")
    monkeypatch.setattr(sys, "argv", ["tool_server", "--token", token, "--port", str(port)])
    import importlib
    import opspectre.sandbox.tool_server as ts
    importlib.reload(ts)
    return ts


@pytest.fixture
def tool_server(monkeypatch):
    return _import_tool_server(monkeypatch)


class TestSafePath:
    def test_valid_workspace_path(self, tool_server):
        path = tool_server._safe_path("/workspace/file.txt")
        assert str(path).startswith("/workspace")

    def test_nested_workspace_path(self, tool_server):
        path = tool_server._safe_path("/workspace/output/reports/scan.txt")
        assert str(path).startswith("/workspace")

    def test_rejects_path_traversal(self, tool_server):
        from fastapi import HTTPException
        with pytest.raises(HTTPException) as exc_info:
            tool_server._safe_path("/workspace/../etc/passwd")
        assert exc_info.value.status_code == 403

    def test_rejects_absolute_escape(self, tool_server):
        from fastapi import HTTPException
        with pytest.raises(HTTPException) as exc_info:
            tool_server._safe_path("/etc/passwd")
        assert exc_info.value.status_code == 403

    def test_rejects_root(self, tool_server):
        from fastapi import HTTPException
        with pytest.raises(HTTPException):
            tool_server._safe_path("/")


class TestSearchFilesInDir:
    def test_finds_match(self, tool_server, tmp_path):
        (tmp_path / "test.txt").write_text("hello world\nfoo bar\n")
        result = tool_server._search_files_in_dir(tmp_path, "hello")
        assert result["success"] is True
        assert "hello" in result["content"]

    def test_no_match(self, tool_server, tmp_path):
        (tmp_path / "test.txt").write_text("nothing here\n")
        result = tool_server._search_files_in_dir(tmp_path, "missing")
        assert result["success"] is True
        assert "No matches found" in result["content"]

    def test_invalid_regex(self, tool_server, tmp_path):
        result = tool_server._search_files_in_dir(tmp_path, "[invalid")
        assert result["success"] is False
        assert "Invalid regex" in result["error"]

    def test_skips_directories(self, tool_server, tmp_path):
        (tmp_path / "subdir").mkdir()
        (tmp_path / "file.txt").write_text("target found\n")
        result = tool_server._search_files_in_dir(tmp_path, "target")
        assert result["success"] is True
        assert "target found" in result["content"]

    def test_multiple_files(self, tool_server, tmp_path):
        (tmp_path / "a.txt").write_text("match here\n")
        (tmp_path / "b.txt").write_text("nope\n")
        (tmp_path / "c.txt").write_text("another match\n")
        result = tool_server._search_files_in_dir(tmp_path, "match")
        assert result["success"] is True
        lines = result["content"].strip().split("\n")
        assert len(lines) == 2


class TestAuthMiddleware:
    def test_health_endpoint_no_auth(self, tool_server):
        from starlette.testclient import TestClient
        client = TestClient(tool_server.app, raise_server_exceptions=False)
        response = client.get("/health")
        assert response.status_code == 200

    def test_execute_requires_auth(self, tool_server):
        from starlette.testclient import TestClient
        client = TestClient(tool_server.app, raise_server_exceptions=False)
        response = client.post("/execute", json={"command": "echo hi"})
        assert response.status_code in (401, 500)

    def test_execute_wrong_token(self, tool_server):
        from starlette.testclient import TestClient
        client = TestClient(tool_server.app, raise_server_exceptions=False)
        response = client.post(
            "/execute",
            json={"command": "echo hi"},
            headers={"Authorization": "Bearer wrong-token"},
        )
        assert response.status_code in (401, 500)

    def test_execute_correct_token(self, tool_server):
        from starlette.testclient import TestClient
        client = TestClient(tool_server.app, raise_server_exceptions=False)
        response = client.post(
            "/execute",
            json={"command": "echo hello"},
            headers={"Authorization": "Bearer test-token"},
        )
        assert response.status_code == 200
        assert "hello" in response.json()["stdout"]


def _make_workspace(tool_server, tmp_path):
    ws = tmp_path / "workspace"
    ws.mkdir()
    monkeypatch_local = pytest.MonkeyPatch()
    monkeypatch_local.setattr(tool_server, "_ALLOWED_ROOT", ws.resolve())
    return ws, monkeypatch_local


class TestFileEndpoints:
    def test_file_read(self, tool_server, tmp_path):
        from starlette.testclient import TestClient
        ws = tmp_path / "workspace"
        ws.mkdir()
        (ws / "file.txt").write_text("hello from workspace")
        original_root = tool_server._ALLOWED_ROOT
        tool_server._ALLOWED_ROOT = ws.resolve()
        try:
            client = TestClient(tool_server.app, raise_server_exceptions=False)
            response = client.post(
                "/file/read",
                json={"path": str(ws / "file.txt")},
                headers={"Authorization": "Bearer test-token"},
            )
            assert response.status_code == 200
            assert "hello from workspace" in response.json()["content"]
        finally:
            tool_server._ALLOWED_ROOT = original_root

    def test_file_write(self, tool_server, tmp_path):
        from starlette.testclient import TestClient
        ws = tmp_path / "workspace"
        ws.mkdir()
        original_root = tool_server._ALLOWED_ROOT
        tool_server._ALLOWED_ROOT = ws.resolve()
        try:
            client = TestClient(tool_server.app, raise_server_exceptions=False)
            response = client.post(
                "/file/write",
                json={"path": str(ws / "new.txt"), "content": "written"},
                headers={"Authorization": "Bearer test-token"},
            )
            assert response.status_code == 200
            assert response.json()["success"] is True
            assert (ws / "new.txt").read_text() == "written"
        finally:
            tool_server._ALLOWED_ROOT = original_root

    def test_file_edit(self, tool_server, tmp_path):
        from starlette.testclient import TestClient
        ws = tmp_path / "workspace"
        ws.mkdir()
        (ws / "edit.txt").write_text("hello old world")
        original_root = tool_server._ALLOWED_ROOT
        tool_server._ALLOWED_ROOT = ws.resolve()
        try:
            client = TestClient(tool_server.app, raise_server_exceptions=False)
            response = client.post(
                "/file/edit",
                json={"path": str(ws / "edit.txt"), "old_text": "old", "new_text": "new"},
                headers={"Authorization": "Bearer test-token"},
            )
            assert response.status_code == 200
            assert response.json()["success"] is True
            assert "new" in (ws / "edit.txt").read_text()
        finally:
            tool_server._ALLOWED_ROOT = original_root

    def test_file_list(self, tool_server, tmp_path):
        from starlette.testclient import TestClient
        ws = tmp_path / "workspace"
        ws.mkdir()
        (ws / "file.txt").write_text("data")
        original_root = tool_server._ALLOWED_ROOT
        tool_server._ALLOWED_ROOT = ws.resolve()
        try:
            client = TestClient(tool_server.app, raise_server_exceptions=False)
            response = client.post(
                "/file/list",
                json={"path": str(ws)},
                headers={"Authorization": "Bearer test-token"},
            )
            assert response.status_code == 200
            assert response.json()["success"] is True
            assert "file.txt" in response.json()["content"]
        finally:
            tool_server._ALLOWED_ROOT = original_root

    def test_file_search(self, tool_server, tmp_path):
        from starlette.testclient import TestClient
        ws = tmp_path / "workspace"
        ws.mkdir()
        (ws / "search.txt").write_text("findme needle here\n")
        original_root = tool_server._ALLOWED_ROOT
        tool_server._ALLOWED_ROOT = ws.resolve()
        try:
            client = TestClient(tool_server.app, raise_server_exceptions=False)
            response = client.post(
                "/file/search",
                json={"pattern": "needle", "path": str(ws)},
                headers={"Authorization": "Bearer test-token"},
            )
            assert response.status_code == 200
            assert response.json()["success"] is True
            assert "needle" in response.json()["content"]
        finally:
            tool_server._ALLOWED_ROOT = original_root
