"""Public demonstration endpoints for the RiskGuard submission demo."""

from typing import Annotated

from app.integrations.disaster.factory import disaster_service
from app.risk_engine.fusion import final_score, level
from app.risk_engine.rules import evaluate
from fastapi import APIRouter, Query
from typing import Annotated
from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.session import get_db_session
from app.repositories.spatial import SpatialRepository
# from app.schemas.domain import ShelterResponse  # adjust if your shelter schema has a different name
from app.schemas.domain import ShelterNearbyResponse

router = APIRouter(prefix="/demo", tags=["Demo"])

from app.repositories.spatial import SpatialRepository
from app.db.session import get_db_session
from app.schemas.domain import ShelterResponse  # adjust import to match your actual shelter response schema

# @router.get("/shelters", response_model=list[ShelterResponse])
# async def demo_shelters(
#     latitude: float,
#     longitude: float,
#     radius_km: float = 25,
#     session: Annotated[AsyncSession, Depends(get_db_session)] = None,
# ) -> list[ShelterResponse]:
#     return await SpatialRepository(session).nearest_shelters(
#         latitude=latitude, longitude=longitude, radius_km=radius_km
#     )
from app.schemas.domain import ShelterNearbyResponse

@router.get(
    "/shelters", response_model=list[ShelterNearbyResponse], summary="Find nearby shelters (demo, no auth)"
)
async def demo_shelters(
    latitude: float,
    longitude: float,
    radius_km: float = 25,
    session: Annotated[AsyncSession, Depends(get_db_session)] = None,
) -> list[ShelterNearbyResponse]:
    radius_metres = radius_km * 1000
    results = await SpatialRepository(session).nearest_shelters(
        latitude, longitude, radius_metres, limit=20
    )
    return [
        ShelterNearbyResponse(
            id=item.shelter.id,
            name=item.shelter.name,
            capacity=item.shelter.capacity,
            current_occupancy=item.shelter.current_occupancy,
            status=item.shelter.status,
            latitude=item.shelter.latitude,
            longitude=item.shelter.longitude,
            facilities=item.shelter.facilities,
            contact_information=item.shelter.contact_information,
            distance_metres=item.distance_metres,
        )
        for item in results
    ]

@router.get("/assess", summary="Demo location risk assessment")
async def assess_demo(
    latitude: Annotated[float, Query(ge=-90, le=90)],
    longitude: Annotated[float, Query(ge=-180, le=180)],
    radius_km: Annotated[float, Query(gt=0, le=500)] = 25.0,
) -> dict[str, object]:
    """Return an unauthenticated demonstration risk assessment."""

    hazards = await disaster_service.fetch_nearby(
        latitude=latitude,
        longitude=longitude,
        radius_km=radius_km,
    )

    scale = {
        "low": 0.25,
        "medium": 0.5,
        "high": 0.75,
        "critical": 1.0,
    }

    inside_hazard = bool(hazards)

    severity = max(
        (
            scale.get(hazard.severity.value, 0.0)
            for hazard in hazards
        ),
        default=0.0,
    )

    rules = evaluate(
        inside_hazard=inside_hazard,
        severity=severity,
        incident_count=0,
    )

    confidence = 0.8 if hazards else 0.45
    score = final_score(rules.score, confidence)

    return {
        "latitude": latitude,
        "longitude": longitude,
        "risk_score": score,
        "risk_level": level(score).value,
        "confidence": confidence,
        "data_source": hazards[0].source if hazards else "NO_HAZARD_DATA",
        "hazards": [
            {
                "hazard_type": hazard.hazard_type,
                "severity": hazard.severity.value,
                "confidence": hazard.confidence,
                "source": hazard.source,
            }
            for hazard in hazards
        ],
        "factors": rules.factors,
    }