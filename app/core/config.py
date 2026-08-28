"""Typed environment configuration with production-safe validation."""

from functools import lru_cache
from typing import Annotated, Literal

from pydantic import AnyHttpUrl, Field, SecretStr, field_validator
from pydantic_settings import BaseSettings, NoDecode, SettingsConfigDict


class Settings(BaseSettings):
    """Configuration sourced exclusively from environment variables and `.env`."""

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    environment: Literal["development", "test", "staging", "production"] = "development"
    debug: bool = False
    log_level: Literal["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"] = "INFO"
    app_name: str = "RiskGuard API"
    api_v1_prefix: str = "/api/v1"
    allowed_hosts: Annotated[list[str], NoDecode] = Field(
        default_factory=lambda: ["localhost", "127.0.0.1"]
    )
    cors_origins: Annotated[list[AnyHttpUrl], NoDecode] = Field(default_factory=list)
    max_request_body_bytes: int = Field(default=1_048_576, ge=1_024, le=10_485_760)

    database_url: str = "postgresql+asyncpg://riskguard:change-me@localhost:5432/riskguard"
    test_database_url: str | None = None
    db_pool_size: int = Field(default=10, ge=1, le=50)
    db_max_overflow: int = Field(default=20, ge=0, le=100)
    db_pool_timeout_seconds: int = Field(default=30, ge=1, le=120)
    db_pool_recycle_seconds: int = Field(default=1_800, ge=60, le=86_400)
    redis_url: str = "redis://localhost:6379/0"
    jwt_secret: SecretStr = SecretStr("replace-with-a-minimum-32-character-random-secret")
    jwt_algorithm: Literal["HS256"] = "HS256"
    access_token_expire_minutes: int = Field(default=15, ge=1, le=120)
    refresh_token_expire_days: int = Field(default=14, ge=1, le=90)
    mapbox_access_token: SecretStr | None = None
    weather_api_key: SecretStr | None = None
    weather_base_url: str | None = None
    external_request_timeout_seconds: float = Field(default=8, ge=1, le=30)
    external_request_max_attempts: int = Field(default=3, ge=1, le=5)
    weather_stale_after_minutes: int = Field(default=90, ge=1, le=1_440)
    firebase_credentials: str | None = None

    @field_validator("allowed_hosts", mode="before")
    @classmethod
    def parse_hosts(cls, value: str | list[str]) -> list[str]:
        """Accept comma-delimited host values from standard environment variables."""
        if isinstance(value, str):
            return [item.strip() for item in value.split(",") if item.strip()]
        return value

    @field_validator("cors_origins", mode="before")
    @classmethod
    def parse_origins(cls, value: str | list[str]) -> list[str]:
        """Accept comma-delimited CORS origins while retaining URL validation."""
        if isinstance(value, str):
            return [item.strip() for item in value.split(",") if item.strip()]
        return value

    @property
    def is_development(self) -> bool:
        """Whether local developer-facing diagnostics may be enabled."""
        return self.environment == "development"

    def validate_production_secrets(self) -> None:
        """Reject known placeholder signing keys in non-development deployments."""
        placeholder = "replace-with-a-minimum-32-character-random-secret"
        secret = self.jwt_secret.get_secret_value()
        if self.environment in {"staging", "production"} and (
            secret == placeholder or len(secret) < 32
        ):
            msg = "JWT_SECRET must be a unique value of at least 32 characters outside development."
            raise ValueError(msg)


@lru_cache
def get_settings() -> Settings:
    """Return one immutable settings object for the process lifetime."""
    settings = Settings()
    settings.validate_production_secrets()
    return settings
