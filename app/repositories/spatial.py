"""Bounded, PostGIS-native spatial queries; never calculate distances in Python."""

from dataclasses import dataclass
from datetime import UTC, datetime

from geoalchemy2 import Geography
from geoalchemy2.elements import WKBElement, WKTElement
from sqlalchemy import Select, cast, func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm.attributes import InstrumentedAttribute
from sqlalchemy.sql.elements import ColumnElement

from app.db.models.hazard import Hazard
from app.db.models.incident import Incident
from app.db.models.shelter import Shelter
from app.db.models.weather_observation import WeatherObservation
from app.db.types import ShelterStatus


def point_wkt(latitude: float, longitude: float) -> WKTElement:
    """Build an SRID-4326 point in longitude/latitude order after caller validation."""
    return WKTElement(f"POINT({longitude} {latitude})", srid=4326)


def geography(
    element: ColumnElement[object] | InstrumentedAttribute[WKBElement] | WKTElement,
) -> ColumnElement[object]:
    """Cast an SRID-4326 geometry expression to geography for metre-correct distance operations."""
    return cast(element, Geography(srid=4326))


@dataclass(frozen=True, slots=True)
class ShelterDistance:
    shelter: Shelter
    distance_metres: float


class SpatialRepository:
    """Repository exposing only indexed, database-executed spatial operations."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def hazards_containing_point(
        self, latitude: float, longitude: float, *, at: datetime | None = None, limit: int = 100
    ) -> list[Hazard]:
        """Find active hazard regions containing a point using ST_Contains."""
        checked_limit = _bounded_limit(limit)
        now = at or datetime.now(UTC)
        point = point_wkt(latitude, longitude)
        statement: Select[tuple[Hazard]] = (
            select(Hazard)
            .where(
                func.ST_Contains(Hazard.geometry, point),
                Hazard.valid_from <= now,
                (Hazard.valid_until.is_(None)) | (Hazard.valid_until >= now),
            )
            .order_by(Hazard.valid_from.desc())
            .limit(checked_limit)
        )
        return list((await self._session.scalars(statement)).all())

    async def hazards_within_radius(
        self, latitude: float, longitude: float, radius_metres: float, *, limit: int = 100
    ) -> list[Hazard]:
        """Find hazard regions within an indexed geography distance radius in metres."""
        statement: Select[tuple[Hazard]] = (
            select(Hazard)
            .where(
                func.ST_DWithin(
                    geography(Hazard.geometry),
                    geography(point_wkt(latitude, longitude)),
                    radius_metres,
                )
            )
            .limit(_bounded_limit(limit))
        )
        return list((await self._session.scalars(statement)).all())

    async def nearest_shelters(
        self, latitude: float, longitude: float, radius_metres: float, *, limit: int = 20
    ) -> list[ShelterDistance]:
        """Find eligible shelters, ordered by PostGIS geography distance in metres."""
        point = geography(point_wkt(latitude, longitude))
        shelter_geography = geography(Shelter.geom)
        distance = func.ST_Distance(shelter_geography, point).label("distance_metres")
        statement = (
            select(Shelter, distance)
            .where(
                Shelter.status.in_([ShelterStatus.AVAILABLE, ShelterStatus.LIMITED]),
                func.ST_DWithin(shelter_geography, point, radius_metres),
            )
            .order_by(distance)
            .limit(_bounded_limit(limit, maximum=100))
        )
        rows = (await self._session.execute(statement)).all()
        return [ShelterDistance(shelter=row[0], distance_metres=float(row[1])) for row in rows]

    async def nearby_incidents(
        self, latitude: float, longitude: float, radius_metres: float, *, limit: int = 100
    ) -> list[Incident]:
        """Find unresolved incidents near a point with ST_DWithin."""
        statement: Select[tuple[Incident]] = (
            select(Incident)
            .where(
                Incident.resolved_at.is_(None),
                func.ST_DWithin(
                    geography(Incident.geom),
                    geography(point_wkt(latitude, longitude)),
                    radius_metres,
                ),
            )
            .order_by(Incident.reported_at.desc())
            .limit(_bounded_limit(limit))
        )
        return list((await self._session.scalars(statement)).all())

    async def nearby_weather_observations(
        self, latitude: float, longitude: float, radius_metres: float, *, limit: int = 20
    ) -> list[WeatherObservation]:
        """Find recent weather observations near a point with ST_DWithin."""
        statement: Select[tuple[WeatherObservation]] = (
            select(WeatherObservation)
            .where(
                func.ST_DWithin(
                    geography(WeatherObservation.geom),
                    geography(point_wkt(latitude, longitude)),
                    radius_metres,
                )
            )
            .order_by(WeatherObservation.observed_at.desc())
            .limit(_bounded_limit(limit, maximum=100))
        )
        return list((await self._session.scalars(statement)).all())


def _bounded_limit(value: int, maximum: int = 500) -> int:
    if value < 1 or value > maximum:
        msg = f"limit must be between 1 and {maximum}."
        raise ValueError(msg)
    return value
