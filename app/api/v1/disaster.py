"""Disaster information API."""

from typing import Annotated

from fastapi import APIRouter, Query

from app.integrations.disaster.factory import disaster_service

router = APIRouter(prefix="/disasters", tags=["Disasters"])


@router.get("/nearby", summary="Get nearby disaster hazards")
async def nearby_disasters(
    latitude: Annotated[float, Query(ge=-90, le=90)],
    longitude: Annotated[float, Query(ge=-180, le=180)],
    radius_km: Annotated[float, Query(gt=0, le=500)] = 25.0,
) -> dict[str, object]:
    """Return normalized disaster information near a location."""

    hazards = await disaster_service.fetch_nearby(
        latitude=latitude,
        longitude=longitude,
        radius_km=radius_km,
    )

    return {
        "status": "DEMO DATA",
        "count": len(hazards),
        "hazards": [
            {
                "hazard_type": hazard.hazard_type,
                "severity": hazard.severity.value,
                "confidence": hazard.confidence,
                "source": hazard.source,
                "valid_from": hazard.valid_from,
                "valid_until": hazard.valid_until,
                "geometry": hazard.geometry,
                "metadata": hazard.metadata,
            }
            for hazard in hazards
        ],
    }