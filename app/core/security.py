"""Password and JWT primitives with no secret-bearing log output."""

from datetime import UTC, datetime, timedelta
from typing import Literal
from uuid import UUID, uuid4

import jwt
from argon2 import PasswordHasher
from argon2.exceptions import InvalidHashError, VerifyMismatchError
from pydantic import BaseModel, ConfigDict

from app.core.config import Settings

PASSWORD_HASHER = PasswordHasher()
TokenKind = Literal["access", "refresh"]


def validate_password_strength(password: str) -> str:
    """Enforce a baseline password policy appropriate for a disaster-management account."""
    if len(password) < 12 or len(password) > 128:
        msg = "Password must be between 12 and 128 characters."
        raise ValueError(msg)
    required_classes = (str.islower, str.isupper, str.isdigit)
    if not all(any(check(character) for character in password) for check in required_classes):
        msg = "Password must include uppercase, lowercase, and numeric characters."
        raise ValueError(msg)
    if password.isalnum():
        msg = "Password must include a symbol."
        raise ValueError(msg)
    return password


class TokenClaims(BaseModel):
    """Validated claims that RiskGuard accepts from a signed JWT."""

    model_config = ConfigDict(extra="forbid")

    sub: UUID
    jti: UUID
    typ: TokenKind
    exp: datetime
    iat: datetime


def hash_password(password: str) -> str:
    """Hash a password with Argon2id; plaintext is never persisted."""
    validate_password_strength(password)
    return PASSWORD_HASHER.hash(password)


def verify_password(password: str, password_hash: str) -> bool:
    """Return false for malformed or non-matching stored hashes without leaking details."""
    try:
        return PASSWORD_HASHER.verify(password_hash, password)
    except (InvalidHashError, VerifyMismatchError):
        return False


def create_token(subject: UUID, kind: TokenKind, settings: Settings) -> tuple[str, UUID, datetime]:
    """Create a short-lived access or rotating refresh JWT."""
    issued_at = datetime.now(UTC)
    expires_at = issued_at + timedelta(
        minutes=settings.access_token_expire_minutes
        if kind == "access"
        else settings.refresh_token_expire_days * 24 * 60
    )
    token_id = uuid4()
    payload = {
        "sub": str(subject),
        "jti": str(token_id),
        "typ": kind,
        "iat": issued_at,
        "exp": expires_at,
    }
    return (
        jwt.encode(
            payload, settings.jwt_secret.get_secret_value(), algorithm=settings.jwt_algorithm
        ),
        token_id,
        expires_at,
    )


def decode_token(token: str, expected_kind: TokenKind, settings: Settings) -> TokenClaims:
    """Verify signature, required claims, and intended token type."""
    payload = jwt.decode(
        token,
        settings.jwt_secret.get_secret_value(),
        algorithms=[settings.jwt_algorithm],
        options={"require": ["sub", "jti", "typ", "iat", "exp"]},
    )
    claims = TokenClaims.model_validate(payload)
    if claims.typ != expected_kind:
        msg = "JWT token type is invalid for this operation."
        raise jwt.InvalidTokenError(msg)
    return claims
