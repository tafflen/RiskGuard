"""Spatially indexed weather observation persistence model."""

from datetime import datetime

from geoalchemy2 import Geometry
from geoalchemy2.elements import WKBElement
from sqlalchemy import CheckConstraint, DateTime, Index, Numeric, String
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base, CreatedAtMixin, UUIDPrimaryKeyMixin


class WeatherObservation(UUIDPrimaryKeyMixin, CreatedAtMixin, Base):
    __tablename__ = "weather_observations"
    __table_args__ = (
        CheckConstraint("latitude >= -90 AND latitude <= 90", name="latitude_range"),
        CheckConstraint("longitude >= -180 AND longitude <= 180", name="longitude_range"),
        CheckConstraint("rainfall_mm IS NULL OR rainfall_mm >= 0", name="rainfall_nonnegative"),
        CheckConstraint(
            "humidity IS NULL OR humidity >= 0 AND humidity <= 100", name="humidity_range"
        ),
        Index("ix_weather_observations_source", "source"),
        Index("ix_weather_observations_observed_at", "observed_at"),
        Index("ix_weather_observations_geom_gist", "geom", postgresql_using="gist"),
    )

    source: Mapped[str] = mapped_column(String(200), nullable=False)
    latitude: Mapped[float] = mapped_column(nullable=False)
    longitude: Mapped[float] = mapped_column(nullable=False)
    geom: Mapped[WKBElement] = mapped_column(
        Geometry("POINT", srid=4326, spatial_index=False), nullable=False
    )
    rainfall_mm: Mapped[float | None] = mapped_column(Numeric(10, 3), nullable=True)
    temperature: Mapped[float | None] = mapped_column(Numeric(6, 3), nullable=True)
    wind_speed: Mapped[float | None] = mapped_column(Numeric(8, 3), nullable=True)
    humidity: Mapped[float | None] = mapped_column(Numeric(5, 2), nullable=True)
    pressure: Mapped[float | None] = mapped_column(Numeric(8, 2), nullable=True)
    observed_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
