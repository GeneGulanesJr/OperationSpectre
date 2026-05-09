"""Run manager - manages run directories and lifecycle."""

import json
import logging
from pathlib import Path
from typing import Any

_log = logging.getLogger("opspectre.run_manager")


class RunManager:
    """Manages OPERATIONSPECTRE run directories."""

    def __init__(self, base_dir: Path | None = None):
        self.base_dir = base_dir or Path.cwd() / "opspectre_runs"
        self.base_dir.mkdir(parents=True, exist_ok=True)

    def list_runs(self) -> list[dict[str, Any]]:
        """List all runs with their summaries."""
        runs = []
        if not self.base_dir.exists():
            return runs

        for run_dir in sorted(self.base_dir.iterdir(), reverse=True):
            if not run_dir.is_dir():
                continue

            summary_file = run_dir / "summary.json"
            if summary_file.exists():
                try:
                    with summary_file.open() as f:
                        summary = json.load(f)
                    runs.append(summary)
                except (json.JSONDecodeError, OSError):
                    runs.append({"name": run_dir.name, "status": "unknown"})
            else:
                runs.append({"name": run_dir.name, "status": "incomplete"})

        return runs

    def get_run(self, name: str) -> dict[str, Any] | None:
        """Get run details by name."""
        if not self.base_dir.exists():
            return None

        for run_dir in self.base_dir.iterdir():
            if run_dir.name == name:
                summary_file = run_dir / "summary.json"
                if summary_file.exists():
                    try:
                        with summary_file.open() as f:
                            return json.load(f)  # type: ignore[no-any-return]
                    except (json.JSONDecodeError, OSError) as e:
                        _log.debug("Failed to read run summary %s: %s", run_dir.name, e)
                return {"name": run_dir.name, "status": "incomplete"}

        return None
