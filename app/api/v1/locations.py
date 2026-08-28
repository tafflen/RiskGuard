"""Privacy-minimized current-location endpoints."""

from typing import Annotated

from app.api.deps import get_current_user
from app.db.models.location import Location
from app.db.models.user import User
from app.db.session import get_db_session
from app.repositories.spatial import point_wkt
from app.schemas.location import LocationCreate, LocationResponse
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

router = APIRouter(prefix="/locations", tags=["Locations"])


@router.post(
    "",
    response_model=LocationResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Store current location",
)
async def create_location(
    payload: LocationCreate,
    user: Annotated[User, Depends(get_current_user)],
    session: Annotated[AsyncSession, Depends(get_db_session)],
) -> LocationResponse:
    """Store an explicit location report; a future cleanup job enforces retention."""
    location = Location(
        user_id=user.id,
        latitude=payload.latitude,
        longitude=payload.longitude,
        accuracy=payload.accuracy,
        geom=point_wkt(payload.latitude, payload.longitude),
        timestamp=payload.timestamp,
    )
    session.add(location)
    await session.flush()
    return LocationResponse.model_validate(location)


@router.get(
    "/latest", response_model=LocationResponse, summary="Get most recent submitted location"
)
async def latest_location(
    user: Annotated[User, Depends(get_current_user)],
    session: Annotated[AsyncSession, Depends(get_db_session)],
) -> LocationResponse:
    """Return only the caller's latest location, never another user's history."""
    location = await session.scalar(
        select(Location)
        .where(Location.user_id == user.id)
        .order_by(Location.timestamp.desc())
        .limit(1)
    )
    if location is None:
        raise HTTPException(status_code=404, detail="No location is available for this user.")
    return LocationResponse.model_validate(location)
