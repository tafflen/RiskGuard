"""Authenticated user endpoints."""

from typing import Annotated

from app.api.deps import get_current_user
from app.db.models.user import User
from app.db.session import get_db_session
from app.schemas.auth import UpdateCurrentUserRequest, UserResponse
from app.services.user_service import UserService
from fastapi import APIRouter, Depends, Response, status
from sqlalchemy.ext.asyncio import AsyncSession

router = APIRouter(prefix="/users", tags=["Users"])


@router.get(
    "/me",
    response_model=UserResponse,
    summary="Get the current user",
    description="Requires a valid bearer access token.",
)
async def read_current_user(user: Annotated[User, Depends(get_current_user)]) -> UserResponse:
    """Return the authenticated user's non-sensitive profile."""
    return UserResponse.model_validate(user)


@router.patch(
    "/me",
    response_model=UserResponse,
    summary="Update the current user",
    description="Updates a display name and/or password. Requires a valid bearer access token.",
)
async def update_current_user(
    payload: UpdateCurrentUserRequest,
    user: Annotated[User, Depends(get_current_user)],
    session: Annotated[AsyncSession, Depends(get_db_session)],
) -> UserResponse:
    """Apply permitted self-service profile changes."""
    updated_user = await UserService(session).update_current_user(user, payload)
    return UserResponse.model_validate(updated_user)


@router.delete(
    "/me",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete the current user account",
    description=(
        "Erases account and device identity data; safety history is detached per retention policy."
    ),
)
async def delete_current_user(
    user: Annotated[User, Depends(get_current_user)],
    session: Annotated[AsyncSession, Depends(get_db_session)],
) -> Response:
    """Execute deliberate account deletion for the authenticated user."""
    await UserService(session).delete_current_user(user)
    return Response(status_code=status.HTTP_204_NO_CONTENT)
