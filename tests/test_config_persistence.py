import json
import os

from opspectre.config import Config


class TestConfigLoadSave:
    def test_load_nonexistent(self, tmp_path):
        Config._config_file_override = tmp_path / "nonexistent.json"
        try:
            data = Config.load()
            assert data == {}
        finally:
            Config._config_file_override = None

    def test_save_and_load(self, tmp_path):
        path = tmp_path / "config.json"
        Config._config_file_override = path
        try:
            Config.save({"env": {"OPSPECTRE_TIMEOUT": "60"}})
            loaded = Config.load()
            assert loaded["env"]["OPSPECTRE_TIMEOUT"] == "60"
        finally:
            Config._config_file_override = None

    def test_load_corrupt_json(self, tmp_path):
        path = tmp_path / "bad.json"
        path.write_text("{bad json")
        Config._config_file_override = path
        try:
            data = Config.load()
            assert data == {}
        finally:
            Config._config_file_override = None

    def test_save_roundtrip_data(self, tmp_path):
        path = tmp_path / "config.json"
        Config._config_file_override = path
        try:
            Config.save({"env": {"OPSPECTRE_IMAGE": "custom:tag", "OPSPECTRE_TIMEOUT": "60"}})
            loaded = Config.load()
            assert loaded["env"]["OPSPECTRE_IMAGE"] == "custom:tag"
            assert loaded["env"]["OPSPECTRE_TIMEOUT"] == "60"
        finally:
            Config._config_file_override = None

    def test_save_sets_permissions(self, tmp_path):
        path = tmp_path / "config.json"
        Config._config_file_override = path
        try:
            Config.save({"env": {"KEY": "secret"}})
            import stat
            mode = path.stat().st_mode & 0o777
            assert mode == 0o600
        finally:
            Config._config_file_override = None


class TestApplySaved:
    def test_applies_env_vars(self, tmp_path, monkeypatch):
        monkeypatch.delenv("OPSPECTRE_TIMEOUT", raising=False)
        path = tmp_path / "config.json"
        path.write_text(json.dumps({"env": {"OPSPECTRE_TIMEOUT": "90"}}))
        Config._config_file_override = path
        try:
            applied = Config.apply_saved(force=True)
            assert "OPSPECTRE_TIMEOUT" in applied
            assert os.environ.get("OPSPECTRE_TIMEOUT") == "90"
        finally:
            Config._config_file_override = None
            monkeypatch.delenv("OPSPECTRE_TIMEOUT", raising=False)

    def test_does_not_override_existing(self, tmp_path, monkeypatch):
        monkeypatch.setenv("OPSPECTRE_TIMEOUT", "30")
        path = tmp_path / "config.json"
        path.write_text(json.dumps({"env": {"OPSPECTRE_TIMEOUT": "90"}}))
        Config._config_file_override = path
        try:
            applied = Config.apply_saved(force=False)
            assert "OPSPECTRE_TIMEOUT" not in applied
            assert os.environ.get("OPSPECTRE_TIMEOUT") == "30"
        finally:
            Config._config_file_override = None
            monkeypatch.delenv("OPSPECTRE_TIMEOUT", raising=False)

    def test_force_overrides_existing(self, tmp_path, monkeypatch):
        monkeypatch.setenv("OPSPECTRE_TIMEOUT", "30")
        path = tmp_path / "config.json"
        path.write_text(json.dumps({"env": {"OPSPECTRE_TIMEOUT": "90"}}))
        Config._config_file_override = path
        try:
            applied = Config.apply_saved(force=True)
            assert "OPSPECTRE_TIMEOUT" in applied
            assert os.environ.get("OPSPECTRE_TIMEOUT") == "90"
        finally:
            Config._config_file_override = None
            monkeypatch.delenv("OPSPECTRE_TIMEOUT", raising=False)

    def test_ignores_unknown_keys(self, tmp_path, monkeypatch):
        monkeypatch.delenv("FAKE_KEY", raising=False)
        path = tmp_path / "config.json"
        path.write_text(json.dumps({"env": {"FAKE_KEY": "value"}}))
        Config._config_file_override = path
        try:
            applied = Config.apply_saved(force=True)
            assert "FAKE_KEY" not in applied
        finally:
            Config._config_file_override = None

    def test_handles_non_dict_env(self, tmp_path):
        path = tmp_path / "config.json"
        path.write_text(json.dumps({"env": "not a dict"}))
        Config._config_file_override = path
        try:
            applied = Config.apply_saved(force=True)
            assert applied == {}
        finally:
            Config._config_file_override = None


class TestSaveCurrent:
    def test_roundtrip(self, tmp_path, monkeypatch):
        monkeypatch.setenv("OPSPECTRE_TIMEOUT", "45")
        path = tmp_path / "config.json"
        Config._config_file_override = path
        try:
            Config.save_current()
            loaded = Config.load()
            assert loaded["env"]["OPSPECTRE_TIMEOUT"] == "45"
        finally:
            Config._config_file_override = None
            monkeypatch.delenv("OPSPECTRE_TIMEOUT", raising=False)

    def test_empty_env_not_saved(self, tmp_path, monkeypatch):
        monkeypatch.setenv("OPSPECTRE_TIMEOUT", "")
        path = tmp_path / "config.json"
        Config._config_file_override = path
        try:
            Config.save_current()
            loaded = Config.load()
            assert "OPSPECTRE_TIMEOUT" not in loaded.get("env", {})
        finally:
            Config._config_file_override = None
            monkeypatch.delenv("OPSPECTRE_TIMEOUT", raising=False)
