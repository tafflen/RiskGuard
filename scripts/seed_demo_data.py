"""Insert clearly labelled simulated data into a configured non-production RiskGuard database."""

import asyncio
from datetime import UTC, datetime, timedelta

from app.core.config import get_settings
from app.db.models import Hazard, Incident, Shelter, WeatherObservation
from app.db.session import get_session_factory
from app.db.types import Severity, ShelterStatus
from app.repositories.spatial import point_wkt
from geoalchemy2.elements import WKTElement
from sqlalchemy import select

DEMO_SOURCE = "DEMO_DATA_NOT_LIVE"


async def seed() -> None:
    """Idempotently seed local development only; production execution is deliberately rejected."""
    settings = get_settings()
    if settings.environment not in {"development", "test"}:
        msg = "Demo data may only be seeded in development or test environments."
        raise RuntimeError(msg)
    now = datetime.now(UTC)
    async with get_session_factory()() as session:
        existing = await session.scalar(
            select(Hazard.id).where(Hazard.source == DEMO_SOURCE).limit(1)
        )
        if existing is not None:
            return
        session.add_all(
            [
                Shelter(
                    name="DEMO Central School Shelter",
                    capacity=300,
                    current_occupancy=80,
                    status=ShelterStatus.AVAILABLE,
                    latitude=22.5729,
                    longitude=88.3638,
                    geom=point_wkt(22.5729, 88.3638),
                    facilities={"water": True, "medical": True, "demo": True},
                    contact_information={"label": "DEMO ONLY"},
                    verified_at=now,
                ),
                Shelter(
                    name="DEMO Riverside Community Hall",
                    capacity=120,
                    current_occupancy=100,
                    status=ShelterStatus.LIMITED,
                    latitude=22.5802,
                    longitude=88.3720,
                    geom=point_wkt(22.5802, 88.3720),
                    facilities={"water": True, "demo": True},
                    contact_information={"label": "DEMO ONLY"},
                    verified_at=now,
                ),
                Shelter(
                    name="DEMO Closed Shelter",
                    capacity=50,
                    current_occupancy=0,
                    status=ShelterStatus.CLOSED,
                    latitude=22.5600,
                    longitude=88.3500,
                    geom=point_wkt(22.5600, 88.3500),
                    facilities={"demo": True},
                    contact_information={"label": "DEMO ONLY"},
                    verified_at=now,
                ),
                Hazard(
                    hazard_type="flood",
                    severity=Severity.HIGH,
                    confidence=0.85,
                    source=DEMO_SOURCE,
                    valid_from=now - timedelta(hours=1),
                    valid_until=now + timedelta(hours=12),
                    geometry=WKTElement(
                        "MULTIPOLYGON(((88.3600 22.5700,88.3800 22.5700,"
                        "88.3800 22.5900,88.3600 22.5900,88.3600 22.5700)))",
                        srid=4326,
                    ),
                    metadata_={"demo": True, "notice": "Simulated, not live disaster data"},
                ),
                Hazard(
                    hazard_type="extreme_rainfall",
                    severity=Severity.MEDIUM,
                    confidence=0.70,
                    source=DEMO_SOURCE,
                    valid_from=now - timedelta(hours=2),
                    valid_until=now + timedelta(hours=6),
                    geometry=WKTElement(
                        "MULTIPOLYGON(((88.3400 22.5500,88.3550 22.5500,"
                        "88.3550 22.5650,88.3400 22.5650,88.3400 22.5500)))",
                        srid=4326,
                    ),
                    metadata_={"demo": True},
                ),
                Incident(
                    incident_type="DEMO road obstruction",
                    severity=Severity.MEDIUM,
                    description="Simulated incident; not live information.",
                    latitude=22.5740,
                    longitude=88.3660,
                    geom=point_wkt(22.5740, 88.3660),
                    source=DEMO_SOURCE,
                    reported_at=now,
                ),
                Incident(
                    incident_type="DEMO power disruption",
                    severity=Severity.LOW,
                    description="Simulated incident; not live information.",
                    latitude=22.5820,
                    longitude=88.3740,
                    geom=point_wkt(22.5820, 88.3740),
                    source=DEMO_SOURCE,
                    reported_at=now,
                ),
                WeatherObservation(
                    source=DEMO_SOURCE,
                    latitude=22.5730,
                    longitude=88.3640,
                    geom=point_wkt(22.5730, 88.3640),
                    rainfall_mm=120.5,
                    temperature=28.2,
                    wind_speed=25.4,
                    humidity=88.0,
                    pressure=1004.2,
                    observed_at=now,
                ),
                WeatherObservation(
                    source=DEMO_SOURCE,
                    latitude=22.5810,
                    longitude=88.3710,
                    geom=point_wkt(22.5810, 88.3710),
                    rainfall_mm=90.0,
                    temperature=28.0,
                    wind_speed=21.0,
                    humidity=84.0,
                    pressure=1005.0,
                    observed_at=now,
                ),
            ]
        )
        await session.commit()


if __name__ == "__main__":
    asyncio.run(seed())
