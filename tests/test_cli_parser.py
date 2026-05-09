import sys
from unittest.mock import patch

import pytest

from opspectre.main import _build_parser, get_version, main


@pytest.fixture(autouse=True)
def _patch_config_apply():
    with patch("opspectre.main.Config.apply_saved"):
        yield


class TestBuildParser:
    def test_no_command_returns_none(self):
        parser = _build_parser()
        args = parser.parse_args([])
        assert args.command is None

    def test_version_flag(self):
        parser = _build_parser()
        with pytest.raises(SystemExit) as exc_info:
            parser.parse_args(["--version"])
        assert exc_info.value.code == 0

    def test_init_command(self):
        parser = _build_parser()
        args = parser.parse_args(["init"])
        assert args.command == "init"

    def test_sandbox_start(self):
        parser = _build_parser()
        args = parser.parse_args(["sandbox", "start"])
        assert args.command == "sandbox"
        assert args.sandbox_action == "start"

    def test_sandbox_stop(self):
        parser = _build_parser()
        args = parser.parse_args(["sandbox", "stop"])
        assert args.sandbox_action == "stop"

    def test_sandbox_status(self):
        parser = _build_parser()
        args = parser.parse_args(["sandbox", "status"])
        assert args.sandbox_action == "status"

    def test_shell_command(self):
        parser = _build_parser()
        args = parser.parse_args(["shell", "ls -la"])
        assert args.command == "shell"
        assert args.shell_command == "ls -la"

    def test_shell_with_timeout(self):
        parser = _build_parser()
        args = parser.parse_args(["shell", "ls", "--timeout", "30"])
        assert args.shell_command == "ls"
        assert args.timeout == 30

    def test_run_command(self):
        parser = _build_parser()
        args = parser.parse_args(["run", "nmap target"])
        assert args.command == "run"
        assert args.run_command == "nmap target"

    def test_file_read(self):
        parser = _build_parser()
        args = parser.parse_args(["file", "read", "/workspace/app.py"])
        assert args.command == "file"
        assert args.file_action == "read"
        assert args.path == "/workspace/app.py"

    def test_file_write(self):
        parser = _build_parser()
        args = parser.parse_args(["file", "write", "/tmp/f.txt", "hello"])
        assert args.file_action == "write"
        assert args.path == "/tmp/f.txt"
        assert args.content == "hello"

    def test_file_edit(self):
        parser = _build_parser()
        args = parser.parse_args(["file", "edit", "f.txt", "old", "new"])
        assert args.file_action == "edit"
        assert args.old == "old"
        assert args.new == "new"

    def test_file_list_default_path(self):
        parser = _build_parser()
        args = parser.parse_args(["file", "list"])
        assert args.file_action == "list"
        assert args.path == "/workspace"

    def test_file_list_custom_path(self):
        parser = _build_parser()
        args = parser.parse_args(["file", "list", "/tmp"])
        assert args.path == "/tmp"

    def test_file_search(self):
        parser = _build_parser()
        args = parser.parse_args(["file", "search", "pattern"])
        assert args.file_action == "search"
        assert args.pattern == "pattern"

    def test_code_python(self):
        parser = _build_parser()
        args = parser.parse_args(["code", "python", "script.py"])
        assert args.command == "code"
        assert args.lang == "python"
        assert args.target == "script.py"

    def test_code_node(self):
        parser = _build_parser()
        args = parser.parse_args(["code", "node", "app.js"])
        assert args.lang == "node"

    def test_browser_navigate(self):
        parser = _build_parser()
        args = parser.parse_args(["browser", "navigate", "https://example.com"])
        assert args.command == "browser"
        assert args.browser_action == "navigate"
        assert args.url == "https://example.com"

    def test_browser_snapshot(self):
        parser = _build_parser()
        args = parser.parse_args(["browser", "snapshot"])
        assert args.browser_action == "snapshot"

    def test_browser_screenshot(self):
        parser = _build_parser()
        args = parser.parse_args(["browser", "screenshot", "https://example.com"])
        assert args.browser_action == "screenshot"
        assert args.url == "https://example.com"

    def test_runs_list(self):
        parser = _build_parser()
        args = parser.parse_args(["runs", "list"])
        assert args.command == "runs"
        assert args.runs_action == "list"

    def test_runs_show(self):
        parser = _build_parser()
        args = parser.parse_args(["runs", "show", "run-001"])
        assert args.runs_action == "show"
        assert args.run_name == "run-001"

    def test_config_set(self):
        parser = _build_parser()
        args = parser.parse_args(["config", "set", "opspectre_timeout", "60"])
        assert args.command == "config"
        assert args.config_action == "set"
        assert args.key == "opspectre_timeout"
        assert args.value == "60"

    def test_config_get(self):
        parser = _build_parser()
        args = parser.parse_args(["config", "get", "opspectre_image"])
        assert args.config_action == "get"
        assert args.key == "opspectre_image"

    def test_json_output_flag(self):
        parser = _build_parser()
        args = parser.parse_args(["--json-output", "init"])
        assert args.json_output is True

    def test_global_timeout_flag(self):
        parser = _build_parser()
        args = parser.parse_args(["--timeout", "60", "init"])
        assert args.timeout == 60

    def test_performance_show(self):
        parser = _build_parser()
        args = parser.parse_args(["performance", "show"])
        assert args.command == "performance"
        assert args.performance_action == "show"

    def test_performance_clear(self):
        parser = _build_parser()
        args = parser.parse_args(["performance", "clear"])
        assert args.performance_action == "clear"


class TestGetVersion:
    def test_returns_nonempty_string(self):
        version = get_version()
        assert isinstance(version, str)
        assert len(version) > 0
        assert "." in version

    def test_fallback_on_missing_version(self):
        import opspectre
        original = opspectre.__version__
        opspectre.__version__ = None
        del opspectre.__version__
        try:
            version = get_version()
            assert isinstance(version, str)
            assert len(version) > 0
        finally:
            opspectre.__version__ = original


class TestMain:
    def test_no_args_exits(self):
        with patch.object(sys, "argv", ["opspectre"]):
            with pytest.raises(SystemExit):
                main()
