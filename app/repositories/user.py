"""Minimal identity persistence operations, separated from authentication policy."""

from typing import cast
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models.refresh_token import RefreshToken
from app.db.models.user import User


class UserRepository:
    """Focused user and refresh-token persistence methods."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def by_email(self, email: str) -> User | None:
        statement = select(User).where(User.email == email)
        return cast(User | None, await self._session.scalar(statement))

    async def by_id(self, user_id: UUID) -> User | None:
        return await self._session.get(User, user_id)

    async def refresh_token(self, token_id: UUID) -> RefreshToken | None:
        return cast(
            RefreshToken | None,
            await self._session.scalar(
                select(RefreshToken).where(RefreshToken.jti == str(token_id))
            ),
        )
