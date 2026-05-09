import argparse
import json
from unittest.mock import MagicMock, patch

from opspectre._ui import _output_mode
from opspectre.cli_commands import (
    _config_get,
    _config_set,
    _present_result,
    _report_run_error,
    _validate_config_key,
    print_result,
)


class TestPresentResult:
    def test_shows_stdout(self, capsys):
        _output_mode.json_output = False
        _present_result({"stdout": "hello world", "stderr": "", "exit_code": 0})
        captured = capsys.readouterr()
        assert "hello world" in captured.out

    def test_shows_stderr(self, capsys):
        _output_mode.json_output = False
        _present_result({"stdout": "", "stderr": "error msg", "exit_code": 1})
        captured = capsys.readouterr()
        assert "error msg" in captured.out

    def test_shows_exit_code_on_failure(self, capsys):
        _output_mode.json_output = False
        _present_result({"stdout": "", "stderr": "", "exit_code": 1})
        captured = capsys.readouterr()
        assert "Exit code: 1" in captured.out

    def test_hides_exit_code_on_success(self, capsys):
        _output_mode.json_output = False
        _present_result({"stdout": "ok", "stderr": "", "exit_code": 0})
        captured = capsys.readouterr()
        assert "Exit code" not in captured.out

    def test_json_mode(self, capsys):
        _output_mode.json_output = True
        try:
            _present_result({"stdout": "out", "stderr": "err", "exit_code": 0})
            captured = capsys.readouterr()
            data = json.loads(captured.out)
            assert data["stdout"] == "out"
        finally:
            _output_mode.json_output = False

    def test_empty_result(self, capsys):
        _output_mode.json_output = False
        _present_result({"stdout": "", "stderr": "", "exit_code": 0})
        captured = capsys.readouterr()
        assert captured.out == ""


class TestPrintResult:
    def test_json_mode(self, capsys):
        _output_mode.json_output = True
        try:
            print_result({"key": "value"})
            captured = capsys.readouterr()
            data = json.loads(captured.out)
            assert data["key"] == "value"
        finally:
            _output_mode.json_output = False

    def test_non_json_mode(self, capsys):
        _output_mode.json_output = False
        print_result({"key": "value"})
        captured = capsys.readouterr()
        assert captured.out == ""


class TestReportRunError:
    def test_text_mode(self, capsys):
        _output_mode.json_output = False
        _report_run_error(RuntimeError("test error"))
        captured = capsys.readouterr()
        assert "test error" in captured.out

    def test_json_mode(self, capsys):
        _output_mode.json_output = True
        try:
            _report_run_error(RuntimeError("test error"))
            captured = capsys.readouterr()
            data = json.loads(captured.out)
            assert data["error"] == "test error"
            assert data["exit_code"] == -1
        finally:
            _output_mode.json_output = False


class TestValidateConfigKey:
    def test_valid_key_returns_true(self):
        with patch("opspectre.cli_commands._exit"):
            result = _validate_config_key("opspectre_timeout")
        assert result is True

    def test_valid_key_all_schema_keys(self):
        from opspectre.config import Config
        with patch("opspectre.cli_commands._exit"):
            for key in Config._SCHEMA:
                assert _validate_config_key(key) is True

    def test_invalid_key_exits(self):
        with patch("opspectre.cli_commands._exit") as mock_exit:
            _validate_config_key("fake_key")
        mock_exit.assert_called_once_with(1)

    def test_invalid_key_does_not_return(self):
        with patch("opspectre.cli_commands._exit") as mock_exit:
            result = _validate_config_key("totally_bogus")
        mock_exit.assert_called_once_with(1)


class TestConfigSet:
    def test_sets_valid_value(self, monkeypatch):
        monkeypatch.delenv("OPSPECTRE_TIMEOUT", raising=False)
        args = argparse.Namespace(key="opspectre_timeout", value="60")
        with patch("opspectre.cli_commands.Config.save_current"):
            _config_set(args)
        assert __import__("os").environ.get("OPSPECTRE_TIMEOUT") == "60"

    def test_rejects_invalid_value(self, monkeypatch):
        monkeypatch.delenv("OPSPECTRE_TIMEOUT", raising=False)
        args = argparse.Namespace(key="opspectre_timeout", value="not_a_number")
        original = __import__("os").environ.get("OPSPECTRE_TIMEOUT")
        with patch("opspectre.cli_commands._exit") as mock_exit:
            _config_set(args)
            mock_exit.assert_called_once_with(1)


class TestConfigGet:
    def test_shows_set_value(self, capsys, monkeypatch):
        monkeypatch.setenv("OPSPECTRE_IMAGE", "test:tag")
        args = argparse.Namespace(key="opspectre_image")
        _config_get(args)
        captured = capsys.readouterr()
        assert "test:tag" in captured.out
