import sys
from unittest.mock import patch

import pytest

from opspectre.core.file_ops import (
    edit_file,
    list_directory,
    read_file,
    search_files,
    write_file,
)
from opspectre.sandbox.docker_runtime import SandboxError


@pytest.fixture
def tool_server_with_workspace(monkeypatch, tmp_path):
    monkeypatch.setenv("OPSPECTRE_SANDBOX_MODE", "true")
    monkeypatch.setattr(sys, "argv", ["tool_server", "--token", "test-token", "--port", "9100"])
    import importlib
    import opspectre.sandbox.tool_server as ts
    importlib.reload(ts)

    ws = tmp_path / "workspace"
    ws.mkdir()
    original_root = ts._ALLOWED_ROOT
    ts._ALLOWED_ROOT = ws.resolve()

    yield ts, ws

    ts._ALLOWED_ROOT = original_root


def _make_runtime_stub(ts_module, ws_path):
    from starlette.testclient import TestClient

    client = TestClient(ts_module.app, raise_server_exceptions=False)

    class _StubRuntime:
        def file_read(self, path):
            resp = client.post("/file/read", json={"path": path},
                               headers={"Authorization": "Bearer test-token"})
            return resp.json()

        def file_write(self, path, content):
            resp = client.post("/file/write", json={"path": path, "content": content},
                               headers={"Authorization": "Bearer test-token"})
            return resp.json()

        def file_edit(self, path, old_text, new_text):
            resp = client.post("/file/edit",
                               json={"path": path, "old_text": old_text, "new_text": new_text},
                               headers={"Authorization": "Bearer test-token"})
            return resp.json()

        def file_list(self, path):
            resp = client.post("/file/list", json={"path": path},
                               headers={"Authorization": "Bearer test-token"})
            return resp.json()

        def file_search(self, pattern, path):
            resp = client.post("/file/search", json={"pattern": pattern, "path": path},
                               headers={"Authorization": "Bearer test-token"})
            return resp.json()

    return _StubRuntime()


class TestReadFileIntegration:
    def test_read_existing_file(self, tool_server_with_workspace):
        ts, ws = tool_server_with_workspace
        (ws / "hello.txt").write_text("hello world")
        stub = _make_runtime_stub(ts, ws)
        with patch("opspectre.core.file_ops.get_runtime", return_value=stub):
            result = read_file(str(ws / "hello.txt"))
        assert result["success"] is True
        assert result["data"]["content"] == "hello world"
        assert result["data"]["path"] == str(ws / "hello.txt")

    def test_read_nonexistent_file(self, tool_server_with_workspace):
        ts, ws = tool_server_with_workspace
        stub = _make_runtime_stub(ts, ws)
        with patch("opspectre.core.file_ops.get_runtime", return_value=stub):
            result = read_file(str(ws / "missing.txt"))
        assert result["success"] is False
        assert result["error"] is not None

    def test_read_empty_file(self, tool_server_with_workspace):
        ts, ws = tool_server_with_workspace
        (ws / "empty.txt").write_text("")
        stub = _make_runtime_stub(ts, ws)
        with patch("opspectre.core.file_ops.get_runtime", return_value=stub):
            result = read_file(str(ws / "empty.txt"))
        assert result["success"] is True
        assert result["data"]["content"] == ""

    def test_read_preserves_multiline(self, tool_server_with_workspace):
        ts, ws = tool_server_with_workspace
        (ws / "multi.txt").write_text("line1\nline2\nline3\n")
        stub = _make_runtime_stub(ts, ws)
        with patch("opspectre.core.file_ops.get_runtime", return_value=stub):
            result = read_file(str(ws / "multi.txt"))
        assert result["success"] is True
        assert "line1\nline2\nline3" in result["data"]["content"]

    def test_read_sandbox_error(self):
        mock_rt = type("R", (), {
            "file_read": lambda s, p: (_ for _ in ()).throw(SandboxError("container down"))
        })()
        with patch("opspectre.core.file_ops.get_runtime", return_value=mock_rt):
            result = read_file("/workspace/test.txt")
        assert result["success"] is False
        assert "container down" in result["error"]


class TestWriteFileIntegration:
    def test_write_new_file(self, tool_server_with_workspace):
        ts, ws = tool_server_with_workspace
        stub = _make_runtime_stub(ts, ws)
        with patch("opspectre.core.file_ops.get_runtime", return_value=stub):
            result = write_file(str(ws / "new.txt"), "hello")
        assert result["success"] is True
        assert result["data"]["bytes_written"] == 5
        assert (ws / "new.txt").read_text() == "hello"

    def test_write_overwrites_existing(self, tool_server_with_workspace):
        ts, ws = tool_server_with_workspace
        (ws / "existing.txt").write_text("old content")
        stub = _make_runtime_stub(ts, ws)
        with patch("opspectre.core.file_ops.get_runtime", return_value=stub):
            result = write_file(str(ws / "existing.txt"), "new content")
        assert result["success"] is True
        assert (ws / "existing.txt").read_text() == "new content"

    def test_write_unicode_content(self, tool_server_with_workspace):
        ts, ws = tool_server_with_workspace
        stub = _make_runtime_stub(ts, ws)
        with patch("opspectre.core.file_ops.get_runtime", return_value=stub):
            result = write_file(str(ws / "unicode.txt"), "héllo wörld 日本語")
        assert result["success"] is True
        assert (ws / "unicode.txt").read_text() == "héllo wörld 日本語"

    def test_write_empty_string(self, tool_server_with_workspace):
        ts, ws = tool_server_with_workspace
        stub = _make_runtime_stub(ts, ws)
        with patch("opspectre.core.file_ops.get_runtime", return_value=stub):
            result = write_file(str(ws / "empty.txt"), "")
        assert result["success"] is True
        assert result["data"]["bytes_written"] == 0


class TestEditFileIntegration:
    def test_edit_replaces_text(self, tool_server_with_workspace):
        ts, ws = tool_server_with_workspace
        (ws / "edit.txt").write_text("hello old world")
        stub = _make_runtime_stub(ts, ws)
        with patch("opspectre.core.file_ops.get_runtime", return_value=stub):
            result = edit_file(str(ws / "edit.txt"), "old", "new")
        assert result["success"] is True
        assert (ws / "edit.txt").read_text() == "hello new world"

    def test_edit_text_not_found(self, tool_server_with_workspace):
        ts, ws = tool_server_with_workspace
        (ws / "edit.txt").write_text("hello world")
        stub = _make_runtime_stub(ts, ws)
        with patch("opspectre.core.file_ops.get_runtime", return_value=stub):
            result = edit_file(str(ws / "edit.txt"), "missing", "replacement")
        assert result["success"] is False

    def test_edit_sandbox_error(self):
        mock_rt = type("R", (), {
            "file_edit": lambda s, p, o, n: (_ for _ in ()).throw(SandboxError("down"))
        })()
        with patch("opspectre.core.file_ops.get_runtime", return_value=mock_rt):
            result = edit_file("/f.txt", "a", "b")
        assert result["success"] is False


class TestListDirectoryIntegration:
    def test_list_shows_files(self, tool_server_with_workspace):
        ts, ws = tool_server_with_workspace
        (ws / "file1.txt").write_text("a")
        (ws / "file2.txt").write_text("b")
        stub = _make_runtime_stub(ts, ws)
        with patch("opspectre.core.file_ops.get_runtime", return_value=stub):
            result = list_directory(str(ws))
        assert result["success"] is True
        content = str(result["data"])
        assert "file1.txt" in content
        assert "file2.txt" in content

    def test_list_default_path(self):
        mock_rt = type("R", (), {"file_list": lambda s, p: {"success": True, "content": "dir/"}})()
        with patch("opspectre.core.file_ops.get_runtime", return_value=mock_rt):
            result = list_directory()
        assert result["success"] is True
        assert result["data"] == "dir/"

    def test_list_empty_directory(self, tool_server_with_workspace):
        ts, ws = tool_server_with_workspace
        empty = ws / "empty_dir"
        empty.mkdir()
        stub = _make_runtime_stub(ts, ws)
        with patch("opspectre.core.file_ops.get_runtime", return_value=stub):
            result = list_directory(str(empty))
        assert result["success"] is True


class TestSearchFilesIntegration:
    def test_search_finds_pattern(self, tool_server_with_workspace):
        ts, ws = tool_server_with_workspace
        (ws / "a.txt").write_text("target string here\n")
        (ws / "b.txt").write_text("nothing relevant\n")
        stub = _make_runtime_stub(ts, ws)
        with patch("opspectre.core.file_ops.get_runtime", return_value=stub):
            result = search_files("target", str(ws))
        assert result["success"] is True
        matches = str(result["data"]["matches"])
        assert "target" in matches

    def test_search_no_matches(self, tool_server_with_workspace):
        ts, ws = tool_server_with_workspace
        (ws / "a.txt").write_text("nothing here\n")
        stub = _make_runtime_stub(ts, ws)
        with patch("opspectre.core.file_ops.get_runtime", return_value=stub):
            result = search_files("nonexistent_pattern", str(ws))
        assert result["success"] is True

    def test_search_sandbox_error(self):
        mock_rt = type("R", (), {
            "file_search": lambda s, q, p: (_ for _ in ()).throw(SandboxError("timeout"))
        })()
        with patch("opspectre.core.file_ops.get_runtime", return_value=mock_rt):
            result = search_files("pattern", "/workspace")
        assert result["success"] is False
