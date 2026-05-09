import json

from opspectre.reporting.run_manager import RunManager


class TestListRuns:
    def test_empty_directory(self, tmp_path):
        base = tmp_path / "empty_runs"
        base.mkdir()
        manager = RunManager(base_dir=base)
        assert manager.list_runs() == []

    def test_lists_runs_with_summaries(self, run_dir_with_summaries):
        manager = RunManager(base_dir=run_dir_with_summaries)
        runs = manager.list_runs()
        assert len(runs) == 3
        names = [r["name"] for r in runs]
        assert "run-001" in names
        assert "run-002" in names
        assert "run-003" in names

    def test_incomplete_run(self, run_dir_incomplete):
        manager = RunManager(base_dir=run_dir_incomplete)
        runs = manager.list_runs()
        assert len(runs) == 1
        assert runs[0]["name"] == "run-partial"
        assert runs[0]["status"] == "incomplete"

    def test_corrupt_summary(self, tmp_path):
        base = tmp_path / "runs"
        base.mkdir()
        d = base / "bad-run"
        d.mkdir()
        (d / "summary.json").write_text("{bad json")
        manager = RunManager(base_dir=base)
        runs = manager.list_runs()
        assert len(runs) == 1
        assert runs[0]["status"] == "unknown"

    def test_sorted_reverse(self, run_dir_with_summaries):
        manager = RunManager(base_dir=run_dir_with_summaries)
        runs = manager.list_runs()
        names = [r["name"] for r in runs]
        assert names == sorted(names, reverse=True)


class TestGetRun:
    def test_exact_match(self, run_dir_with_summaries):
        manager = RunManager(base_dir=run_dir_with_summaries)
        run = manager.get_run("run-001")
        assert run is not None
        assert run["name"] == "run-001"
        assert run["status"] == "completed"

    def test_no_match(self, run_dir_with_summaries):
        manager = RunManager(base_dir=run_dir_with_summaries)
        assert manager.get_run("nonexistent") is None

    def test_incomplete_run(self, run_dir_incomplete):
        manager = RunManager(base_dir=run_dir_incomplete)
        run = manager.get_run("run-partial")
        assert run is not None
        assert run["status"] == "incomplete"

    def test_empty_directory(self, tmp_path):
        base = tmp_path / "empty"
        base.mkdir()
        manager = RunManager(base_dir=base)
        assert manager.get_run("anything") is None


class TestRunManagerInit:
    def test_creates_base_dir(self, tmp_path):
        base = tmp_path / "auto_created"
        assert not base.exists()
        RunManager(base_dir=base)
        assert base.exists()

    def test_default_base_dir(self):
        manager = RunManager()
        assert manager.base_dir.name == "opspectre_runs"
