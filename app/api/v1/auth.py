"""Public identity endpoints."""

from typing import Annotated

from app.core.config import Settings, get_settings
from app.db.session import get_db_session
from app.schemas.auth import (
    LoginRequest,
    LogoutRequest,
    RefreshRequest,
    RegisterRequest,
    TokenResponse,
    UserResponse,
)
from app.services.auth_service import AuthService
from fastapi import APIRouter, Depends, Response, status
from sqlalchemy.ext.asyncio import AsyncSession

router = APIRouter(prefix="/auth", tags=["Auth"])


def auth_service(
    session: Annotated[AsyncSession, Depends(get_db_session)],
    settings: Annotated[Settings, Depends(get_settings)],
) -> AuthService:
    """Construct a request-scoped authentication service."""
    return AuthService(session, settings)


@router.post(
    "/register",
    response_model=UserResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Register a citizen account",
    description=(
        "Creates an account with an Argon2id password verifier. Authentication is not required."
    ),
)
async def register(
    payload: RegisterRequest, service: Annotated[AuthService, Depends(auth_service)]
) -> UserResponse:
    """Register a new citizen account."""
    return UserResponse.model_validate(await service.register(payload))


@router.post(
    "/login",
    response_model=TokenResponse,
    summary="Authenticate and issue a token pair",
    description="Returns a short-lived access JWT and a rotating refresh JWT.",
)
async def login(
    payload: LoginRequest, service: Annotated[AuthService, Depends(auth_service)]
) -> TokenResponse:
    """Authenticate an active user."""
    return await service.login(payload)


@router.post(
    "/refresh",
    response_model=TokenResponse,
    summary="Rotate a refresh token",
    description="Revokes the supplied refresh token and returns a fresh access/refresh pair.",
)
async def refresh(
    payload: RefreshRequest, service: Annotated[AuthService, Depends(auth_service)]
) -> TokenResponse:
    """Rotate a refresh JWT."""
    return await service.refresh(payload.refresh_token)


@router.post(
    "/logout",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Revoke a refresh token",
    description="Invalidates the supplied refresh token. Authentication is not required.",
)
async def logout(
    payload: LogoutRequest, service: Annotated[AuthService, Depends(auth_service)]
) -> Response:
    """Perform explicit logout by revoking refresh-token server state."""
    await service.logout(payload.refresh_token)
    return Response(status_code=status.HTTP_204_NO_CONTENT)
