"""Read-only hazard discovery APIs backed by PostGIS."""

from datetime import UTC, datetime
from typing import Annotated
from uuid import UUID

from app.api.deps import get_current_user
from app.db.models.hazard import Hazard
from app.db.models.user import User
from app.db.session import get_db_session
from app.repositories.spatial import SpatialRepository
from app.schemas.domain import HazardResponse
from app.schemas.geospatial import RadiusQuery
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

router = APIRouter(prefix="/hazards", tags=["Hazards"])


def response(hazard: Hazard) -> HazardResponse:
    return HazardResponse(
        id=hazard.id,
        hazard_type=hazard.hazard_type,
        severity=hazard.severity,
        confidence=float(hazard.confidence),
        source=hazard.source,
        valid_from=hazard.valid_from,
        valid_until=hazard.valid_until,
        metadata=hazard.metadata_,
    )


@router.get(
    "/nearby", response_model=list[HazardResponse], summary="Find hazards near a coordinate"
)
async def nearby(
    query: Annotated[RadiusQuery, Depends()],
    _: Annotated[User, Depends(get_current_user)],
    session: Annotated[AsyncSession, Depends(get_db_session)],
) -> list[HazardResponse]:
    return [
        response(item)
        for item in await SpatialRepository(session).hazards_within_radius(
            query.latitude, query.longitude, query.radius_metres, limit=query.limit
        )
    ]


@router.get("/active", response_model=list[HazardResponse], summary="List active hazards")
async def active(
    _: Annotated[User, Depends(get_current_user)],
    session: Annotated[AsyncSession, Depends(get_db_session)],
    limit: int = 100,
) -> list[HazardResponse]:
    now = datetime.now(UTC)
    rows = (
        await session.scalars(
            select(Hazard)
            .where(
                Hazard.valid_from <= now,
                (Hazard.valid_until.is_(None)) | (Hazard.valid_until >= now),
            )
            .order_by(Hazard.valid_from.desc())
            .limit(min(max(limit, 1), 100))
        )
    ).all()
    return [response(item) for item in rows]


@router.get("/{hazard_id}", response_model=HazardResponse, summary="Get a hazard by ID")
async def get_hazard(
    hazard_id: UUID,
    _: Annotated[User, Depends(get_current_user)],
    session: Annotated[AsyncSession, Depends(get_db_session)],
) -> HazardResponse:
    item = await session.get(Hazard, hazard_id)
    if item is None:
        raise HTTPException(status_code=404, detail="Hazard not found.")
    return response(item)
