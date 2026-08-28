"""Unit tests for the password and JWT safety primitives."""

from datetime import UTC, datetime, timedelta
from uuid import uuid4

import jwt
import pytest
from app.core.config import Settings
from app.core.security import create_token, decode_token, hash_password, verify_password
from app.schemas.auth import RegisterRequest


@pytest.fixture
def settings() -> Settings:
    return Settings(environment="test", jwt_secret="a-test-secret-that-is-longer-than-32-chars")


def test_password_hashes_and_verifies() -> None:
    password_hash = hash_password("A-valid-test-password-123!")

    assert password_hash != "A-valid-test-password-123!"
    assert verify_password("A-valid-test-password-123!", password_hash)
    assert not verify_password("incorrect password", password_hash)


def test_password_policy_rejects_weak_password() -> None:
    with pytest.raises(ValueError, match="uppercase"):
        RegisterRequest(email="citizen@example.com", password="alllowercase!1", full_name="Citizen")


def test_access_token_round_trip(settings: Settings) -> None:
    subject = uuid4()
    token, _, _ = create_token(subject, "access", settings)

    claims = decode_token(token, "access", settings)

    assert claims.sub == subject
    assert claims.typ == "access"


def test_refresh_token_cannot_be_used_as_access_token(settings: Settings) -> None:
    token, _, _ = create_token(uuid4(), "refresh", settings)

    with pytest.raises(jwt.InvalidTokenError, match="type"):
        decode_token(token, "access", settings)


def test_expired_token_is_rejected(settings: Settings) -> None:
    payload = {
        "sub": str(uuid4()),
        "jti": str(uuid4()),
        "typ": "access",
        "iat": datetime.now(UTC) - timedelta(minutes=2),
        "exp": datetime.now(UTC) - timedelta(minutes=1),
    }
    token = jwt.encode(
        payload, settings.jwt_secret.get_secret_value(), algorithm=settings.jwt_algorithm
    )

    with pytest.raises(jwt.ExpiredSignatureError):
        decode_token(token, "access", settings)
