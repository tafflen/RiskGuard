"""Database integration tests executed only against the dedicated PostGIS test database."""

from datetime import UTC, datetime, timedelta

import pytest
from app.db.models import Hazard, Incident, Location, RiskAssessment, Shelter, User
from app.db.types import RiskLevel, Severity, ShelterStatus, UserRole
from app.repositories.spatial import SpatialRepository, point_wkt
from geoalchemy2.elements import WKTElement
from sqlalchemy import text
from sqlalchemy.exc import IntegrityError

pytestmark = pytest.mark.integration


async def test_postgis_is_available(db_session) -> None:
    version = await db_session.scalar(text("SELECT PostGIS_Version()"))
    assert isinstance(version, str)
    assert version


async def test_user_unique_email_constraint(db_session) -> None:
    db_session.add(
        User(
            email="citizen@example.test",
            password_hash="not-a-password",
            full_name="Citizen",
            role=UserRole.CITIZEN,
        )
    )
    await db_session.commit()
    db_session.add(
        User(
            email="citizen@example.test",
            password_hash="not-a-password",
            full_name="Citizen Two",
            role=UserRole.CITIZEN,
        )
    )
    with pytest.raises(IntegrityError):
        await db_session.commit()


async def test_coordinate_and_geometry_constraints(db_session) -> None:
    db_session.add(
        Location(
            latitude=22.57,
            longitude=88.36,
            accuracy=5,
            geom=point_wkt(22.57, 88.36),
            timestamp=datetime.now(UTC),
        )
    )
    await db_session.commit()
    db_session.add(
        Location(
            latitude=91,
            longitude=88.36,
            accuracy=5,
            geom=point_wkt(91, 88.36),
            timestamp=datetime.now(UTC),
        )
    )
    with pytest.raises(IntegrityError):
        await db_session.commit()
    await db_session.rollback()
    db_session.add(
        Location(
            latitude=22.57,
            longitude=181,
            accuracy=5,
            geom=point_wkt(22.57, 181),
            timestamp=datetime.now(UTC),
        )
    )
    with pytest.raises(IntegrityError):
        await db_session.commit()


async def test_spatial_repositories_and_constraints(db_session) -> None:
    now = datetime.now(UTC)
    hazard = Hazard(
        hazard_type="flood",
        severity=Severity.HIGH,
        confidence=0.9,
        source="TEST",
        valid_from=now - timedelta(minutes=5),
        valid_until=now + timedelta(minutes=5),
        geometry=WKTElement(
            "MULTIPOLYGON(((88.35 22.55,88.39 22.55,88.39 22.59,88.35 22.59,88.35 22.55)))",
            srid=4326,
        ),
        metadata_={},
    )
    nearest = Shelter(
        name="Nearest",
        capacity=100,
        current_occupancy=0,
        status=ShelterStatus.AVAILABLE,
        latitude=22.570,
        longitude=88.360,
        geom=point_wkt(22.570, 88.360),
        facilities={},
        contact_information={},
    )
    farther = Shelter(
        name="Farther",
        capacity=100,
        current_occupancy=0,
        status=ShelterStatus.AVAILABLE,
        latitude=22.590,
        longitude=88.390,
        geom=point_wkt(22.590, 88.390),
        facilities={},
        contact_information={},
    )
    incident = Incident(
        incident_type="test",
        severity=Severity.MEDIUM,
        latitude=22.571,
        longitude=88.361,
        geom=point_wkt(22.571, 88.361),
        source="TEST",
        reported_at=now,
    )
    db_session.add_all([hazard, nearest, farther, incident])
    await db_session.commit()
    repository = SpatialRepository(db_session)
    assert [item.id for item in await repository.hazards_containing_point(22.57, 88.36)] == [
        hazard.id
    ]
    shelters = await repository.nearest_shelters(22.570, 88.360, 10_000)
    assert shelters[0].shelter.id == nearest.id
    assert [item.id for item in await repository.nearby_incidents(22.57, 88.36, 500)] == [
        incident.id
    ]


async def test_risk_constraints(db_session) -> None:
    assessment = RiskAssessment(
        latitude=22.57,
        longitude=88.36,
        geom=point_wkt(22.57, 88.36),
        risk_score=50,
        risk_level=RiskLevel.MEDIUM,
        model_version="test",
        confidence=0.8,
        factors={},
    )
    db_session.add(assessment)
    await db_session.commit()
    db_session.add(
        RiskAssessment(
            latitude=22.57,
            longitude=88.36,
            geom=point_wkt(22.57, 88.36),
            risk_score=101,
            risk_level=RiskLevel.HIGH,
            model_version="test",
            confidence=1.1,
            factors={},
        )
    )
    with pytest.raises(IntegrityError):
        await db_session.commit()
