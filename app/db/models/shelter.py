"""Shelter capacity and availability persistence model."""

from datetime import datetime
from typing import Any

from geoalchemy2 import Geometry
from geoalchemy2.elements import WKBElement
from sqlalchemy import CheckConstraint, Enum, Index, Integer, String
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base, TimestampMixin, UUIDPrimaryKeyMixin
from app.db.types import ShelterStatus


class Shelter(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "shelters"
    __table_args__ = (
        CheckConstraint("latitude >= -90 AND latitude <= 90", name="latitude_range"),
        CheckConstraint("longitude >= -180 AND longitude <= 180", name="longitude_range"),
        CheckConstraint("capacity >= 0", name="capacity_nonnegative"),
        CheckConstraint("current_occupancy >= 0", name="occupancy_nonnegative"),
        CheckConstraint("current_occupancy <= capacity", name="occupancy_within_capacity"),
        Index("ix_shelters_status", "status"),
        Index("ix_shelters_geom_gist", "geom", postgresql_using="gist"),
    )

    name: Mapped[str] = mapped_column(String(300), nullable=False)
    capacity: Mapped[int] = mapped_column(Integer, nullable=False)
    current_occupancy: Mapped[int] = mapped_column(
        Integer, nullable=False, default=0, server_default="0"
    )
    status: Mapped[ShelterStatus] = mapped_column(
        Enum(ShelterStatus, name="shelter_status", native_enum=False), nullable=False
    )
    latitude: Mapped[float] = mapped_column(nullable=False)
    longitude: Mapped[float] = mapped_column(nullable=False)
    geom: Mapped[WKBElement] = mapped_column(
        Geometry("POINT", srid=4326, spatial_index=False), nullable=False
    )
    facilities: Mapped[dict[str, Any]] = mapped_column(JSONB, nullable=False, default=dict)
    contact_information: Mapped[dict[str, Any]] = mapped_column(JSONB, nullable=False, default=dict)
    verified_at: Mapped[datetime | None] = mapped_column(nullable=True)
