from unittest.mock import MagicMock, patch

from opspectre.core.file_ops import (
    edit_file,
    list_directory,
    read_file,
    search_files,
    write_file,
)
from opspectre.sandbox.docker_runtime import SandboxError


class TestReadFile:
    def test_success(self):
        mock_rt = MagicMock()
        mock_rt.file_read.return_value = {"success": True, "content": "hello"}
        with patch("opspectre.core.file_ops.get_runtime", return_value=mock_rt):
            result = read_file("/workspace/test.txt")
        assert result["success"] is True
        assert result["data"]["content"] == "hello"

    def test_failure(self):
        mock_rt = MagicMock()
        mock_rt.file_read.return_value = {"success": False, "error": "not found"}
        with patch("opspectre.core.file_ops.get_runtime", return_value=mock_rt):
            result = read_file("/workspace/missing.txt")
        assert result["success"] is False
        assert "not found" in result["error"]

    def test_sandbox_error(self):
        mock_rt = MagicMock()
        mock_rt.file_read.side_effect = SandboxError("container down")
        with patch("opspectre.core.file_ops.get_runtime", return_value=mock_rt):
            result = read_file("/workspace/test.txt")
        assert result["success"] is False
        assert "container down" in result["error"]


class TestWriteFile:
    def test_success(self):
        mock_rt = MagicMock()
        mock_rt.file_write.return_value = {"success": True}
        with patch("opspectre.core.file_ops.get_runtime", return_value=mock_rt):
            result = write_file("/workspace/out.txt", "data")
        assert result["success"] is True
        assert result["data"]["bytes_written"] == 4

    def test_failure(self):
        mock_rt = MagicMock()
        mock_rt.file_write.return_value = {"success": False, "error": "disk full"}
        with patch("opspectre.core.file_ops.get_runtime", return_value=mock_rt):
            result = write_file("/workspace/out.txt", "data")
        assert result["success"] is False


class TestEditFile:
    def test_success(self):
        mock_rt = MagicMock()
        mock_rt.file_edit.return_value = {"success": True}
        with patch("opspectre.core.file_ops.get_runtime", return_value=mock_rt):
            result = edit_file("/workspace/f.txt", "old", "new")
        assert result["success"] is True

    def test_not_found(self):
        mock_rt = MagicMock()
        mock_rt.file_edit.return_value = {"success": False, "error": "old_text not found"}
        with patch("opspectre.core.file_ops.get_runtime", return_value=mock_rt):
            result = edit_file("/workspace/f.txt", "old", "new")
        assert result["success"] is False


class TestListDirectory:
    def test_success(self):
        mock_rt = MagicMock()
        mock_rt.file_list.return_value = {"success": True, "content": "  file.txt  (10 bytes)"}
        with patch("opspectre.core.file_ops.get_runtime", return_value=mock_rt):
            result = list_directory("/workspace")
        assert result["success"] is True

    def test_default_path(self):
        mock_rt = MagicMock()
        mock_rt.file_list.return_value = {"success": True, "content": "dir/"}
        with patch("opspectre.core.file_ops.get_runtime", return_value=mock_rt):
            result = list_directory()
        mock_rt.file_list.assert_called_once_with("/workspace")


class TestSearchFiles:
    def test_success(self):
        mock_rt = MagicMock()
        mock_rt.file_search.return_value = {"success": True, "content": "f.txt:1: match"}
        with patch("opspectre.core.file_ops.get_runtime", return_value=mock_rt):
            result = search_files("pattern", "/workspace")
        assert result["success"] is True

    def test_sandbox_error(self):
        mock_rt = MagicMock()
        mock_rt.file_search.side_effect = SandboxError("timeout")
        with patch("opspectre.core.file_ops.get_runtime", return_value=mock_rt):
            result = search_files("pattern", "/workspace")
        assert result["success"] is False
