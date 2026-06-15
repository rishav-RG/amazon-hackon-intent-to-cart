"""Unit tests for app/config.py — Config class validation."""

import os

import pytest
from pydantic import ValidationError

from app.config import Config


# Minimal valid env kwargs for constructing Config directly
VALID_ENV = {
    "DATABASE_URL": "postgresql+asyncpg://user:pass@localhost:5432/testdb",
    "REDIS_URL": "redis://localhost:6379/0",
    "APP_ENV": "development",
}


def _make_config(monkeypatch, **overrides):
    """Create a Config instance with controlled env vars (no .env file influence).

    Clears relevant env vars and only sets what's explicitly passed.
    """
    # Clear all config-related env vars to prevent .env file bleed-through
    for key in ("DATABASE_URL", "REDIS_URL", "CORS_ORIGINS", "APP_ENV", "DEBUG"):
        monkeypatch.delenv(key, raising=False)

    env = {**VALID_ENV, **overrides}
    # Use _env_file=None to prevent .env file loading in tests
    return Config(_env_file=None, **env)


def _make_config_missing(monkeypatch, **kwargs):
    """Create a Config instance with specific kwargs only (no defaults, no .env)."""
    for key in ("DATABASE_URL", "REDIS_URL", "CORS_ORIGINS", "APP_ENV", "DEBUG"):
        monkeypatch.delenv(key, raising=False)
    return Config(_env_file=None, **kwargs)


class TestConfigValidFields:
    """Config loads correctly with valid values."""

    def test_minimal_valid_config(self, monkeypatch):
        cfg = _make_config(monkeypatch)
        assert cfg.DATABASE_URL == VALID_ENV["DATABASE_URL"]
        assert cfg.REDIS_URL == VALID_ENV["REDIS_URL"]
        assert cfg.APP_ENV == "development"
        assert cfg.DEBUG is False
        assert cfg.CORS_ORIGINS == ["http://localhost:3000"]

    def test_all_fields_provided(self, monkeypatch):
        cfg = _make_config(
            monkeypatch,
            CORS_ORIGINS="http://a.com,http://b.com",
            DEBUG=True,
        )
        assert cfg.CORS_ORIGINS == ["http://a.com", "http://b.com"]
        assert cfg.DEBUG is True

    def test_app_env_staging(self, monkeypatch):
        cfg = _make_config(monkeypatch, APP_ENV="staging")
        assert cfg.APP_ENV == "staging"

    def test_app_env_production(self, monkeypatch):
        cfg = _make_config(monkeypatch, APP_ENV="production")
        assert cfg.APP_ENV == "production"


class TestConfigCorsOriginsParsing:
    """CORS_ORIGINS is parsed from comma-separated string."""

    def test_single_origin(self, monkeypatch):
        cfg = _make_config(monkeypatch, CORS_ORIGINS="http://localhost:3000")
        assert cfg.CORS_ORIGINS == ["http://localhost:3000"]

    def test_multiple_origins(self, monkeypatch):
        cfg = _make_config(monkeypatch, CORS_ORIGINS="http://a.com, http://b.com, http://c.com")
        assert cfg.CORS_ORIGINS == ["http://a.com", "http://b.com", "http://c.com"]

    def test_trailing_commas_ignored(self, monkeypatch):
        cfg = _make_config(monkeypatch, CORS_ORIGINS="http://a.com,,http://b.com,")
        assert cfg.CORS_ORIGINS == ["http://a.com", "http://b.com"]

    def test_list_passthrough(self, monkeypatch):
        cfg = _make_config(monkeypatch, CORS_ORIGINS=["http://x.com", "http://y.com"])
        assert cfg.CORS_ORIGINS == ["http://x.com", "http://y.com"]


class TestConfigMissingRequired:
    """Missing required fields raise validation errors (Req 1.3)."""

    def test_missing_database_url(self, monkeypatch):
        with pytest.raises(ValidationError) as exc_info:
            _make_config_missing(monkeypatch, REDIS_URL="redis://localhost:6379/0", APP_ENV="development")
        assert "DATABASE_URL" in str(exc_info.value)

    def test_missing_redis_url(self, monkeypatch):
        with pytest.raises(ValidationError) as exc_info:
            _make_config_missing(monkeypatch, DATABASE_URL="postgresql+asyncpg://x", APP_ENV="development")
        assert "REDIS_URL" in str(exc_info.value)

    def test_missing_app_env(self, monkeypatch):
        with pytest.raises(ValidationError) as exc_info:
            _make_config_missing(
                monkeypatch,
                DATABASE_URL="postgresql+asyncpg://x",
                REDIS_URL="redis://localhost:6379/0",
            )
        assert "APP_ENV" in str(exc_info.value)


class TestConfigInvalidValues:
    """Invalid constrained values raise validation errors (Req 1.4)."""

    def test_invalid_app_env(self, monkeypatch):
        with pytest.raises(ValidationError) as exc_info:
            _make_config(monkeypatch, APP_ENV="testing")
        assert "APP_ENV" in str(exc_info.value)

    def test_debug_invalid_value(self, monkeypatch):
        with pytest.raises(ValidationError) as exc_info:
            _make_config(monkeypatch, DEBUG="not_a_bool")
        assert "DEBUG" in str(exc_info.value)


class TestConfigSingleton:
    """The module exposes a singleton settings instance (Req 1.5)."""

    def test_settings_is_config_instance(self):
        """settings is already instantiated at module level and is a Config instance."""
        from app.config import settings

        assert isinstance(settings, Config)

    def test_settings_has_required_attributes(self):
        """settings exposes all expected configuration fields."""
        from app.config import settings

        assert hasattr(settings, "DATABASE_URL")
        assert hasattr(settings, "REDIS_URL")
        assert hasattr(settings, "CORS_ORIGINS")
        assert hasattr(settings, "APP_ENV")
        assert hasattr(settings, "DEBUG")
