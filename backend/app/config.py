"""Application configuration module using Pydantic BaseSettings."""

import json
from typing import Any, Literal

from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic_settings import DotEnvSettingsSource, EnvSettingsSource


class _CorsAwareEnvSource(EnvSettingsSource):
    """Env source that handles comma-separated CORS_ORIGINS without JSON error."""

    def decode_complex_value(self, field_name: str, field: Any, value: Any) -> Any:
        if field_name == "CORS_ORIGINS" and isinstance(value, str):
            try:
                return json.loads(value)
            except (json.JSONDecodeError, ValueError):
                return value
        return super().decode_complex_value(field_name, field, value)


class _CorsAwareDotEnvSource(DotEnvSettingsSource):
    """DotEnv source that handles comma-separated CORS_ORIGINS without JSON error."""

    def decode_complex_value(self, field_name: str, field: Any, value: Any) -> Any:
        if field_name == "CORS_ORIGINS" and isinstance(value, str):
            try:
                return json.loads(value)
            except (json.JSONDecodeError, ValueError):
                return value
        return super().decode_complex_value(field_name, field, value)


class Config(BaseSettings):
    """Centralized configuration loaded from environment variables and .env file.

    Required fields (no defaults):
        DATABASE_URL: PostgreSQL async connection string.
        REDIS_URL: Redis connection string.
        APP_ENV: One of "development", "staging", or "production".

    Optional fields (have defaults):
        CORS_ORIGINS: List of allowed CORS origins, parsed from comma-separated env var.
        DEBUG: Enable debug mode.
    """

    DATABASE_URL: str
    REDIS_URL: str
    CORS_ORIGINS: list[str] = ["http://localhost:3000"]
    APP_ENV: Literal["development", "staging", "production"]
    DEBUG: bool = False

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
    )

    @field_validator("CORS_ORIGINS", mode="before")
    @classmethod
    def parse_cors_origins(cls, v: object) -> list[str]:
        """Parse CORS_ORIGINS from a comma-separated string or pass through a list."""
        if isinstance(v, str):
            return [origin.strip() for origin in v.split(",") if origin.strip()]
        if isinstance(v, list):
            return v
        return v

    @classmethod
    def settings_customise_sources(cls, settings_cls, init_settings, env_settings, dotenv_settings, file_secret_settings):
        """Customise env/dotenv sources to handle comma-separated CORS_ORIGINS."""
        # Build a CORS-aware env source with the same configuration
        cors_env = _CorsAwareEnvSource(settings_cls)

        # Build a CORS-aware dotenv source preserving the original dotenv config
        cors_dotenv = _CorsAwareDotEnvSource(
            settings_cls,
            env_file=dotenv_settings.env_file,
            env_file_encoding=dotenv_settings.env_file_encoding,
        )

        return (
            init_settings,
            cors_env,
            cors_dotenv,
            file_secret_settings,
        )


settings = Config()
