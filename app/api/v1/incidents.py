# ruff: noqa: E501
"""Read-only incident intelligence endpoints using PostGIS repository queries."""

from typing import Annotated

from app.api.deps import get_current_user
from app.db.models.incident import Incident
from app.db.models.user import User
from app.db.session import get_db_session
from app.repositories.spatial import SpatialRepository
from app.schemas.domain import IncidentResponse
from app.schemas.geospatial import RadiusQuery
from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

router = APIRouter(prefix="/incidents", tags=["Incidents"])


@router.get(
    "/nearby", response_model=list[IncidentResponse], summary="Find nearby unresolved incidents"
)
async def nearby(
    query: Annotated[RadiusQuery, Depends()],
    _: Annotated[User, Depends(get_current_user)],
    session: Annotated[AsyncSession, Depends(get_db_session)],
) -> list[IncidentResponse]:
    return [
        IncidentResponse.model_validate(item)
        for item in await SpatialRepository(session).nearby_incidents(
            query.latitude, query.longitude, query.radius_metres, limit=query.limit
        )
    ]


@router.get(
    "/active", response_model=list[IncidentResponse], summary="List active unresolved incidents"
)
async def active(
    _: Annotated[User, Depends(get_current_user)],
    session: Annotated[AsyncSession, Depends(get_db_session)],
    limit: int = 100,
) -> list[IncidentResponse]:
    rows = (
        await session.scalars(
            select(Incident)
            .where(Incident.resolved_at.is_(None))
            .order_by(Incident.reported_at.desc())
            .limit(min(max(limit, 1), 100))
        )
    ).all()
    return [IncidentResponse.model_validate(item) for item in rows]
