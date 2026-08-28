"""Authentication policy and refresh-token rotation."""

from datetime import UTC, datetime

import jwt
from app.core.config import Settings
from app.core.exceptions import RiskGuardError
from app.core.security import (
    TokenClaims,
    create_token,
    decode_token,
    hash_password,
    verify_password,
)
from app.db.models.refresh_token import RefreshToken
from app.db.models.user import User
from app.db.types import UserRole
from app.repositories.user import UserRepository
from app.schemas.auth import LoginRequest, RegisterRequest, TokenResponse
from pydantic import ValidationError
from sqlalchemy.ext.asyncio import AsyncSession


class AuthService:
    """Identity workflow; all writes are committed by the request session dependency."""

    def __init__(self, session: AsyncSession, settings: Settings) -> None:
        self._session = session
        self._settings = settings
        self._users = UserRepository(session)

    async def register(self, payload: RegisterRequest) -> User:
        """Create a citizen identity with an Argon2id password verifier."""
        email = str(payload.email).lower()
        if await self._users.by_email(email) is not None:
            raise RiskGuardError(
                "EMAIL_ALREADY_REGISTERED", "An account already exists for this email.", 409
            )
        user = User(
            email=email,
            password_hash=hash_password(payload.password),
            full_name=payload.full_name,
            role=UserRole.CITIZEN,
        )
        self._session.add(user)
        await self._session.flush()
        return user

    async def login(self, payload: LoginRequest) -> TokenResponse:
        """Authenticate without exposing which credential component failed."""
        user = await self._users.by_email(str(payload.email).lower())
        if (
            user is None
            or not user.is_active
            or not verify_password(payload.password, user.password_hash)
        ):
            raise RiskGuardError("INVALID_CREDENTIALS", "Email or password is invalid.", 401)
        return await self._issue_tokens(user)

    async def refresh(self, refresh_token: str) -> TokenResponse:
        """Rotate a valid, non-revoked refresh token into a fresh token pair."""
        claims = _refresh_claims(refresh_token, self._settings)
        record = await self._users.refresh_token(claims.jti)
        if (
            record is None
            or record.revoked_at is not None
            or record.expires_at <= datetime.now(UTC)
        ):
            raise RiskGuardError(
                "INVALID_REFRESH_TOKEN", "Refresh token is invalid or expired.", 401
            )
        user = await self._users.by_id(claims.sub)
        if user is None or not user.is_active:
            raise RiskGuardError(
                "INVALID_REFRESH_TOKEN", "Refresh token is invalid or expired.", 401
            )
        record.revoked_at = datetime.now(UTC)
        return await self._issue_tokens(user)

    async def logout(self, refresh_token: str) -> None:
        """Revoke the supplied refresh token; invalid tokens receive the same safe response."""
        claims = _refresh_claims(refresh_token, self._settings)
        record = await self._users.refresh_token(claims.jti)
        if record is None or record.revoked_at is not None:
            raise RiskGuardError(
                "INVALID_REFRESH_TOKEN", "Refresh token is invalid or expired.", 401
            )
        record.revoked_at = datetime.now(UTC)

    async def _issue_tokens(self, user: User) -> TokenResponse:
        access_token, _, _ = create_token(user.id, "access", self._settings)
        refresh_token, refresh_id, refresh_expiry = create_token(user.id, "refresh", self._settings)
        self._session.add(
            RefreshToken(user_id=user.id, jti=str(refresh_id), expires_at=refresh_expiry)
        )
        await self._session.flush()
        return TokenResponse(
            access_token=access_token,
            refresh_token=refresh_token,
            expires_in=self._settings.access_token_expire_minutes * 60,
        )


def _refresh_claims(token: str, settings: Settings) -> TokenClaims:
    """Convert JWT implementation errors into a safe refresh-token response."""
    try:
        return decode_token(token, "refresh", settings)
    except (jwt.PyJWTError, ValidationError) as exc:
        raise RiskGuardError(
            "INVALID_REFRESH_TOKEN", "Refresh token is invalid or expired.", 401
        ) from exc
