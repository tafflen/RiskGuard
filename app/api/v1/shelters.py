"""Hazard-aware shelter discovery API foundation."""

from typing import Annotated
from uuid import UUID

from app.api.deps import get_current_user
from app.db.models.shelter import Shelter
from app.db.models.user import User
from app.db.session import get_db_session
from app.repositories.spatial import SpatialRepository
from app.schemas.domain import ShelterNearbyResponse, ShelterResponse
from app.schemas.geospatial import RadiusQuery
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

router = APIRouter(prefix="/shelters", tags=["Shelters"])


@router.get(
    "/nearby", response_model=list[ShelterNearbyResponse], summary="Find available nearby shelters"
)
async def nearby(
    query: Annotated[RadiusQuery, Depends()],
    _: Annotated[User, Depends(get_current_user)],
    session: Annotated[AsyncSession, Depends(get_db_session)],
) -> list[ShelterNearbyResponse]:
    results = await SpatialRepository(session).nearest_shelters(
        query.latitude, query.longitude, query.radius_metres, limit=query.limit
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


@router.get("/{shelter_id}", response_model=ShelterResponse, summary="Get a shelter by ID")
async def get_shelter(
    shelter_id: UUID,
    _: Annotated[User, Depends(get_current_user)],
    session: Annotated[AsyncSession, Depends(get_db_session)],
) -> ShelterResponse:
    item = await session.get(Shelter, shelter_id)
    if item is None:
        raise HTTPException(status_code=404, detail="Shelter not found.")
    return ShelterResponse.model_validate(item)
