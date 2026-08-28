# ruff: noqa: E501
"""Stored weather observation read API; provider acquisition is a later phase."""

from typing import Annotated

from app.api.deps import get_current_user
from app.db.models.user import User
from app.db.session import get_db_session
from app.repositories.spatial import SpatialRepository
from app.schemas.domain import WeatherObservationResponse
from app.schemas.geospatial import RadiusQuery
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

router = APIRouter(prefix="/weather", tags=["Weather"])


@router.get(
    "/current",
    response_model=WeatherObservationResponse,
    summary="Get nearest stored weather observation",
)
async def current(
    query: Annotated[RadiusQuery, Depends()],
    _: Annotated[User, Depends(get_current_user)],
    session: Annotated[AsyncSession, Depends(get_db_session)],
) -> WeatherObservationResponse:
    """Returns stored source data only; never invents a current weather result."""
    observations = await SpatialRepository(session).nearby_weather_observations(
        query.latitude, query.longitude, query.radius_metres, limit=1
    )
    if not observations:
        raise HTTPException(
            status_code=404, detail="No weather observation is available for this area."
        )
    return WeatherObservationResponse.model_validate(observations[0])
