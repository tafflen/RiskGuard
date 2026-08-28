"""Reusable authentication and role dependencies for future API resources."""

from collections.abc import Awaitable, Callable
from typing import Annotated

import jwt
from app.core.config import Settings, get_settings
from app.core.exceptions import RiskGuardError
from app.core.security import decode_token
from app.db.models.user import User
from app.db.session import get_db_session
from app.db.types import UserRole
from app.repositories.user import UserRepository
from fastapi import Depends
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from pydantic import ValidationError
from sqlalchemy.ext.asyncio import AsyncSession

bearer_scheme = HTTPBearer(auto_error=False)
DatabaseSession = Annotated[AsyncSession, Depends(get_db_session)]


async def get_current_user(
    session: DatabaseSession,
    credentials: Annotated[HTTPAuthorizationCredentials | None, Depends(bearer_scheme)],
    settings: Annotated[Settings, Depends(get_settings)],
) -> User:
    """Resolve an active user from a valid bearer access token."""
    if credentials is None or credentials.scheme.lower() != "bearer":
        raise RiskGuardError("AUTHENTICATION_REQUIRED", "Authentication is required.", 401)
    try:
        claims = decode_token(credentials.credentials, "access", settings)
    except (jwt.PyJWTError, ValidationError):
        raise RiskGuardError(
            "INVALID_ACCESS_TOKEN", "Access token is invalid or expired.", 401
        ) from None
    user = await UserRepository(session).by_id(claims.sub)
    if user is None or not user.is_active:
        raise RiskGuardError("INVALID_ACCESS_TOKEN", "Access token is invalid or expired.", 401)
    return user


def require_roles(*roles: UserRole) -> Callable[[User], Awaitable[User]]:
    """Return a dependency that gates an endpoint to explicit database roles."""

    async def dependency(user: Annotated[User, Depends(get_current_user)]) -> User:
        if user.role not in roles:
            raise RiskGuardError("FORBIDDEN", "You do not have permission for this operation.", 403)
        return user

    return dependency


def require_role(role: UserRole) -> Callable[[User], Awaitable[User]]:
    """Singular convenience form for endpoints that require exactly one role."""
    return require_roles(role)
