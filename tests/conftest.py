import json
from pathlib import Path
from unittest.mock import MagicMock

import pytest


@pytest.fixture
def tmp_config_dir(tmp_path):
    override = tmp_path / "opspectre-config"
    override.mkdir()
    return override


@pytest.fixture
def mock_runtime():
    runtime = MagicMock()
    runtime.status.return_value = "running"
    runtime.execute.return_value = {"stdout": "", "stderr": "", "exit_code": 0}
    runtime.file_read.return_value = {"success": True, "content": "file contents"}
    runtime.file_write.return_value = {"success": True}
    runtime.file_edit.return_value = {"success": True, "replacements": 1}
    runtime.file_list.return_value = {"success": True, "content": "  file.txt  (10 bytes)"}
    runtime.file_search.return_value = {"success": True, "content": "file.txt:1: match"}
    runtime.start.return_value = {
        "container_name": "opspectre-default",
        "container_id": "abc123",
        "api_url": "http://127.0.0.1:48081",
    }
    runtime.stop.return_value = True
    runtime.is_connected.return_value = True
    return runtime


@pytest.fixture
def run_dir_with_summaries(tmp_path):
    base = tmp_path / "runs"
    base.mkdir()
    for name, status in [("run-001", "completed"), ("run-002", "failed"), ("run-003", "completed")]:
        d = base / name
        d.mkdir()
        (d / "summary.json").write_text(json.dumps({"name": name, "status": status}))
    return base


@pytest.fixture
def run_dir_incomplete(tmp_path):
    base = tmp_path / "runs"
    base.mkdir()
    d = base / "run-partial"
    d.mkdir()
    return base
