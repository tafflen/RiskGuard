"""Tests for Phase 1 configuration guarantees."""

import pytest
from app.core.config import Settings


def test_comma_delimited_settings_are_parsed() -> None:
    settings = Settings(
        allowed_hosts="api.example.test, localhost",
        cors_origins="https://mobile.example.test,http://localhost:3000",
    )

    assert settings.allowed_hosts == ["api.example.test", "localhost"]
    assert [str(origin) for origin in settings.cors_origins] == [
        "https://mobile.example.test/",
        "http://localhost:3000/",
    ]


def test_production_rejects_placeholder_jwt_secret() -> None:
    settings = Settings(environment="production")

    with pytest.raises(ValueError, match="JWT_SECRET"):
        settings.validate_production_secrets()


def test_development_allows_placeholder_jwt_secret() -> None:
    settings = Settings(environment="development")

    settings.validate_production_secrets()
