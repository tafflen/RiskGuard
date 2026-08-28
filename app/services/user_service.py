"""Authenticated self-service profile and account-deletion operations."""

from app.core.security import hash_password
from app.db.models.user import User
from app.db.models.user_device import UserDevice
from app.schemas.auth import UpdateCurrentUserRequest
from sqlalchemy import delete
from sqlalchemy.ext.asyncio import AsyncSession


class UserService:
    """Mutates only the authenticated user's permitted identity data."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def update_current_user(self, user: User, payload: UpdateCurrentUserRequest) -> User:
        """Update profile fields and re-hash a replacement password if supplied."""
        if payload.full_name is not None:
            user.full_name = payload.full_name
        if payload.new_password is not None:
            user.password_hash = hash_password(payload.new_password)
        await self._session.flush()
        return user

    async def delete_current_user(self, user: User) -> None:
        """Erase identity and device rows while retaining detached safety-history records.

        Locations and risk assessments use ON DELETE SET NULL from Phase 2. User devices use
        RESTRICT to prevent accidental deletes, so this explicit user-requested erasure removes
        them first.
        """
        await self._session.execute(delete(UserDevice).where(UserDevice.user_id == user.id))
        await self._session.delete(user)
        await self._session.flush()
