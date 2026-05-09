import os

import pytest

from opspectre.config import Config, ConfigError


class TestCoerceInt:
    def test_valid_int(self):
        assert Config._coerce_int("42", "test") == 42

    def test_negative(self):
        assert Config._coerce_int("-1", "test") == -1

    def test_zero(self):
        assert Config._coerce_int("0", "test") == 0

    def test_invalid_string(self):
        with pytest.raises(ConfigError, match="must be an integer"):
            Config._coerce_int("abc", "test")

    def test_none(self):
        with pytest.raises(ConfigError):
            Config._coerce_int(None, "test")

    def test_float_string(self):
        with pytest.raises(ConfigError):
            Config._coerce_int("3.14", "test")


class TestCoerceBool:
    def test_true(self):
        assert Config._coerce_bool("true", "test") is True

    def test_false(self):
        assert Config._coerce_bool("false", "test") is False

    def test_one(self):
        assert Config._coerce_bool("1", "test") is True

    def test_zero(self):
        assert Config._coerce_bool("0", "test") is False

    def test_yes(self):
        assert Config._coerce_bool("yes", "test") is True

    def test_on(self):
        assert Config._coerce_bool("on", "test") is True

    def test_mixed_case(self):
        assert Config._coerce_bool("True", "test") is True
        assert Config._coerce_bool("FALSE", "test") is False
        assert Config._coerce_bool("Yes", "test") is True

    def test_random_string(self):
        assert Config._coerce_bool("maybe", "test") is False


class TestCoerceStr:
    def test_passthrough(self):
        assert Config._coerce_str("hello", "test") == "hello"

    def test_empty(self):
        assert Config._coerce_str("", "test") == ""


class TestValidateBounds:
    def test_within_range(self):
        Config._validate_bounds("test", 50, 1, 100)

    def test_below_min(self):
        with pytest.raises(ConfigError, match="below minimum"):
            Config._validate_bounds("test", 0, 1, 100)

    def test_above_max(self):
        with pytest.raises(ConfigError, match="exceeds maximum"):
            Config._validate_bounds("test", 200, 1, 100)

    def test_at_min(self):
        Config._validate_bounds("test", 1, 1, 100)

    def test_at_max(self):
        Config._validate_bounds("test", 100, 1, 100)

    def test_none_bounds(self):
        Config._validate_bounds("test", 9999, None, None)


class TestTypedGet:
    def test_unknown_key(self):
        with pytest.raises(ConfigError, match="Unknown config key"):
            Config._typed_get("nonexistent_key", str)

    def test_wrong_type(self):
        with pytest.raises(ConfigError, match="is int, not str"):
            Config._typed_get("opspectre_timeout", str)

    def test_valid_int_from_env(self, monkeypatch):
        monkeypatch.setenv("OPSPECTRE_TIMEOUT", "60")
        assert Config._typed_get("opspectre_timeout", int) == 60

    def test_invalid_int_from_env(self, monkeypatch):
        monkeypatch.setenv("OPSPECTRE_TIMEOUT", "abc")
        with pytest.raises(ConfigError, match="must be an integer"):
            Config._typed_get("opspectre_timeout", int)

    def test_out_of_range(self, monkeypatch):
        monkeypatch.setenv("OPSPECTRE_TIMEOUT", "99999")
        with pytest.raises(ConfigError, match="exceeds maximum"):
            Config._typed_get("opspectre_timeout", int)


class TestGet:
    def test_returns_string(self, monkeypatch):
        monkeypatch.setenv("OPSPECTRE_IMAGE", "custom:tag")
        assert Config.get("opspectre_image") == "custom:tag"

    def test_default_value(self, monkeypatch):
        monkeypatch.delenv("OPSPECTRE_IMAGE", raising=False)
        result = Config.get("opspectre_image")
        assert result == "opspectre-full:latest"

    def test_unknown_key(self):
        assert Config.get("totally_unknown_key") is None

    def test_tracked_names_matches_schema(self):
        assert set(Config._tracked_names()) == set(Config._SCHEMA.keys())


class TestGetInt:
    def test_valid(self, monkeypatch):
        monkeypatch.setenv("OPSPECTRE_TIMEOUT", "30")
        assert Config.get_int("opspectre_timeout") == 30

    def test_invalid(self, monkeypatch):
        monkeypatch.setenv("OPSPECTRE_TIMEOUT", "bad")
        with pytest.raises(ConfigError):
            Config.get_int("opspectre_timeout")


class TestGetBool:
    def test_true(self, monkeypatch):
        monkeypatch.setenv("OPSPECTRE_PERFORMANCE_LOGGING", "true")
        assert Config.get_bool("opspectre_performance_logging") is True

    def test_false(self, monkeypatch):
        monkeypatch.setenv("OPSPECTRE_PERFORMANCE_LOGGING", "false")
        assert Config.get_bool("opspectre_performance_logging") is False


class TestGetStr:
    def test_valid(self, monkeypatch):
        monkeypatch.setenv("OPSPECTRE_IMAGE", "myimage:v2")
        assert Config.get_str("opspectre_image") == "myimage:v2"
