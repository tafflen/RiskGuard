"""User persistence model; password handling belongs to the identity phase."""

from typing import TYPE_CHECKING

from sqlalchemy import Boolean, Enum, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, TimestampMixin, UUIDPrimaryKeyMixin
from app.db.types import UserRole

if TYPE_CHECKING:
    from app.db.models.location import Location
    from app.db.models.refresh_token import RefreshToken
    from app.db.models.risk_assessment import RiskAssessment
    from app.db.models.user_device import UserDevice


class User(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "users"

    email: Mapped[str] = mapped_column(String(320), nullable=False, unique=True, index=True)
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    full_name: Mapped[str] = mapped_column(String(200), nullable=False)
    role: Mapped[UserRole] = mapped_column(
        Enum(UserRole, name="user_role", native_enum=False),
        nullable=False,
        default=UserRole.CITIZEN,
    )
    is_active: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=True, server_default="true"
    )

    devices: Mapped[list["UserDevice"]] = relationship(back_populates="user", passive_deletes=True)
    locations: Mapped[list["Location"]] = relationship(back_populates="user", passive_deletes=True)
    risk_assessments: Mapped[list["RiskAssessment"]] = relationship(
        back_populates="user", passive_deletes=True
    )
    refresh_tokens: Mapped[list["RefreshToken"]] = relationship(
        back_populates="user", cascade="all, delete-orphan", passive_deletes=True
    )
