"""Time-bounded geographic hazard persistence model."""

from datetime import datetime
from typing import Any

from geoalchemy2 import Geometry
from geoalchemy2.elements import WKBElement
from sqlalchemy import CheckConstraint, DateTime, Enum, Index, Numeric, String
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base, TimestampMixin, UUIDPrimaryKeyMixin
from app.db.types import Severity


class Hazard(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    """A hazard is active only from valid_from through valid_until (if set)."""

    __tablename__ = "hazards"
    __table_args__ = (
        CheckConstraint("confidence >= 0 AND confidence <= 1", name="confidence_range"),
        CheckConstraint("valid_until IS NULL OR valid_until >= valid_from", name="validity_range"),
        Index("ix_hazards_hazard_type", "hazard_type"),
        Index("ix_hazards_severity", "severity"),
        Index("ix_hazards_valid_from", "valid_from"),
        Index("ix_hazards_valid_until", "valid_until"),
        Index("ix_hazards_source", "source"),
        Index("ix_hazards_geometry_gist", "geometry", postgresql_using="gist"),
    )

    # A validated string permits future provider-specific hazard types without a schema migration.
    hazard_type: Mapped[str] = mapped_column(String(100), nullable=False)
    severity: Mapped[Severity] = mapped_column(
        Enum(Severity, name="hazard_severity", native_enum=False), nullable=False
    )
    confidence: Mapped[float] = mapped_column(Numeric(4, 3), nullable=False)
    source: Mapped[str] = mapped_column(String(200), nullable=False)
    valid_from: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    valid_until: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    geometry: Mapped[WKBElement] = mapped_column(
        Geometry("MULTIPOLYGON", srid=4326, spatial_index=False), nullable=False
    )
    metadata_: Mapped[dict[str, Any]] = mapped_column(
        "metadata", JSONB, nullable=False, default=dict
    )
