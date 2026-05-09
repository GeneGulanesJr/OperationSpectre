import contextlib
import json
import os
from pathlib import Path
from typing import Any, ClassVar


class ConfigError(Exception):
    """Raised when a config value fails validation."""


class Config:
    """Configuration Manager for OPERATIONSPECTRE.

    Settings are defined in a typed schema (_SCHEMA).  The generic
    ``get()`` classmethod still returns raw strings (for backward
    compatibility), but callers that need a specific type should use
    ``get_int()`` or ``get_str()`` which validate against the schema
    and raise ``ConfigError`` on bad values.
    """

    # ── typed schema (single source of truth for all config keys) ──────────────────
    # key -> (type, default, min_value | None, max_value | None)
    _SCHEMA: ClassVar[dict[str, tuple[type, Any, Any, Any]]] = {
        "opspectre_image": (str, "opspectre-full:latest", None, None),
        "opspectre_timeout": (int, 120, 1, 3_600),
        "opspectre_output_limit": (int, 1_048_576, 1024, 268_435_456),  # 1 KB - 256 MB
        "tool_server_port": (int, 48081, 1024, 65535),
        "opspectre_performance_logging": (bool, True, None, None),
        "opspectre_metrics_interval": (int, 60, 10, 3600),
        "opspectre_slow_operation_threshold": (int, 5000, 1000, 30000),  # milliseconds
    }

    _CANONICAL_NAMES = tuple(_SCHEMA.keys())

    # ── type coercion dispatch ───────────────────────────────────────

    @staticmethod
    def _coerce_int(raw: str, name: str) -> int:
        try:
            return int(raw)
        except (ValueError, TypeError) as exc:
            raise ConfigError(
                f"Config key {name!r} must be an integer, got {raw!r}"
            ) from exc

    @staticmethod
    def _coerce_bool(raw: str, _name: str) -> bool:
        return raw.lower() in ("true", "1", "yes", "on")

    @staticmethod
    def _coerce_str(raw: str, _name: str) -> str:
        return raw

    _COERCERS: ClassVar[dict[type, Any]] = {
        int: _coerce_int.__func__,
        bool: _coerce_bool.__func__,
        str: _coerce_str.__func__,
    }

    @classmethod
    def _validate_bounds(cls, name: str, value: Any, min_val: Any, max_val: Any) -> None:
        """Raise ConfigError if value is outside the allowed range."""
        if min_val is not None and value < min_val:
            raise ConfigError(f"Config key {name!r} = {value} is below minimum {min_val}")
        if max_val is not None and value > max_val:
            raise ConfigError(f"Config key {name!r} = {value} exceeds maximum {max_val}")

    # ── defaults (kept as class attributes for backward compat) ──────
    # Derived from _SCHEMA — keep in sync when adding new keys.
    opspectre_image: str = _SCHEMA["opspectre_image"][1]       # type: ignore[assignment]
    opspectre_timeout: str = str(_SCHEMA["opspectre_timeout"][1])
    opspectre_output_limit: str = str(_SCHEMA["opspectre_output_limit"][1])
    tool_server_port: str = str(_SCHEMA["tool_server_port"][1])
    opspectre_performance_logging: str = str(_SCHEMA["opspectre_performance_logging"][1])
    opspectre_metrics_interval: str = str(_SCHEMA["opspectre_metrics_interval"][1])
    opspectre_slow_operation_threshold: str = str(_SCHEMA["opspectre_slow_operation_threshold"][1])

    _config_file_override: Path | None = None

    # ── raw access (returns str | None, backward compat) ─────────────

    @classmethod
    def _tracked_names(cls) -> list[str]:
        """Return all config key names derived from _SCHEMA.

        This is the single source of truth for which keys are persisted
        by save_current() and loaded by apply_saved().
        """
        return list(cls._SCHEMA.keys())

    @classmethod
    def get(cls, name: str) -> str | None:
        """Return the raw string value for *name*, or ``None``.

        Checks the environment first, then falls back to the _SCHEMA
        default (converted to ``str``).  Returns ``None`` for unknown keys.
        """
        if name in cls._SCHEMA:
            _type, default, _min, _max = cls._SCHEMA[name]
            default_str = str(default) if default is not None else None
        else:
            default_str = None
        return os.getenv(name.upper(), default_str)

    # ── typed access with validation ─────────────────────────────────

    @classmethod
    def get_int(cls, name: str) -> int:
        """Return *name* as ``int``, validated against the schema.

        Raises ``ConfigError`` if the key is unknown, not a valid
        integer, or outside the allowed range.
        """
        return cls._typed_get(name, int)  # type: ignore[return-value]

    @classmethod
    def get_str(cls, name: str) -> str:
        """Return *name* as ``str``, validated against the schema.

        Raises ``ConfigError`` if the key is unknown or the value is
        empty when the schema requires a non-empty string.
        """
        return cls._typed_get(name, str)  # type: ignore[return-value]

    @classmethod
    def get_bool(cls, name: str, default: bool | None = None) -> bool:
        """Return *name* as ``bool``, validated against the schema.

        Raises ``ConfigError`` if the key is unknown or the value is
        not a valid boolean.
        """
        return cls._typed_get(name, bool)  # type: ignore[return-value]

    @classmethod
    def _typed_get(cls, name: str, expected_type: type) -> Any:
        """Validate and return a config value from the environment.

        Parses the raw string from the environment according to the
        schema type, then checks min/max bounds.  Raises
        ``ConfigError`` on any validation failure.
        """
        if name not in cls._SCHEMA:
            raise ConfigError(f"Unknown config key: {name!r}")

        schema = cls._SCHEMA[name]
        if schema[0] is not expected_type:
            raise ConfigError(
                f"Config key {name!r} is {schema[0].__name__}, not {expected_type.__name__}"
            )

        default = schema[1]
        raw = os.getenv(name.upper(), str(default) if default is not None else None)

        if raw is None:
            raise ConfigError(f"Config key {name!r} has no value and no default")

        coercer = cls._COERCERS.get(schema[0], None)
        if coercer:
            value: Any = coercer(raw, name)
        else:
            value = raw
        cls._validate_bounds(name, value, schema[2], schema[3])

        return value

    # ── persistence ──────────────────────────────────────────────────

    @classmethod
    def config_dir(cls) -> Path:
        return Path.home() / ".opspectre"

    @classmethod
    def config_file(cls) -> Path:
        if cls._config_file_override is not None:
            return cls._config_file_override
        return cls.config_dir() / "cli-config.json"

    @classmethod
    def load(cls) -> dict[str, Any]:
        path = cls.config_file()
        if not path.exists():
            return {}
        try:
            with path.open("r", encoding="utf-8") as f:
                data: dict[str, Any] = json.load(f)
                return data
        except (json.JSONDecodeError, OSError):
            return {}

    @classmethod
    def save(cls, config: dict[str, Any]) -> bool:
        config_path = cls.config_file()
        try:
            cls.config_dir().mkdir(parents=True, exist_ok=True)
            with config_path.open("w", encoding="utf-8") as f:
                json.dump(config, f, indent=2)
        except OSError:
            return False
        with contextlib.suppress(OSError):
            config_path.chmod(0o600)
        return True

    @classmethod
    def apply_saved(cls, force: bool = False) -> dict[str, str]:
        saved = cls.load()
        env_vars = saved.get("env", {})
        if not isinstance(env_vars, dict):
            env_vars = {}

        applied = {}
        for var_name, var_value in env_vars.items():
            if var_name in {n.upper() for n in cls._tracked_names()} and (
                force or var_name not in os.environ
            ):
                os.environ[var_name] = var_value
                applied[var_name] = var_value

        return applied

    @classmethod
    def save_current(cls) -> bool:
        existing = cls.load().get("env", {})
        merged = dict(existing)

        for var_name in cls._tracked_names():
            upper_name = var_name.upper()
            value = os.getenv(upper_name)
            if value is None:
                pass
            elif value == "":
                merged.pop(upper_name, None)
            else:
                merged[upper_name] = value

        return cls.save({"env": merged})
