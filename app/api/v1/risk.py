# ruff: noqa: E501
"""Risk assessment and persistence APIs."""

from typing import Annotated

from app.api.deps import get_current_user
from app.db.models.risk_assessment import RiskAssessment
from app.db.models.user import User
from app.db.session import get_db_session
from app.integrations.disaster.factory import disaster_service
from app.repositories.spatial import SpatialRepository, point_wkt
from app.risk_engine.fusion import final_score, level
from app.risk_engine.rules import evaluate
from app.schemas.risk import RiskAssessRequest, RiskHistoryResponse
from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

router = APIRouter(prefix="/risk", tags=["Risk"])


@router.post("/assess", response_model=RiskHistoryResponse, summary="Assess location risk")
async def assess(
    payload: RiskAssessRequest,
    user: Annotated[User, Depends(get_current_user)],
    session: Annotated[AsyncSession, Depends(get_db_session)],
) -> RiskHistoryResponse:
    """Calculate deterministic explainable risk from available hazard and incident evidence."""

    spatial = SpatialRepository(session)

    # Existing persisted evidence.
    persisted_hazards = await spatial.hazards_containing_point(
        payload.latitude,
        payload.longitude,
        limit=10,
    )

    incidents = await spatial.nearby_incidents(
        payload.latitude,
        payload.longitude,
        5_000,
        limit=20,
    )

    # External/demo disaster evidence.
    external_hazards = await disaster_service.fetch_nearby(
        latitude=payload.latitude,
        longitude=payload.longitude,
        radius_km=25.0,
    )

    scale = {
        "low": 0.25,
        "medium": 0.5,
        "high": 0.75,
        "critical": 1.0,
    }

    # Prefer persisted hazards when available; otherwise use the
    # explicitly marked disaster-provider result.
    if persisted_hazards:
        inside_hazard = True
        severity = max(
            (scale.get(item.severity.value, 0.0) for item in persisted_hazards),
            default=0.0,
        )
        data_source = "PERSISTED"
    elif external_hazards:
        inside_hazard = True
        severity = max(
            (scale.get(item.severity.value, 0.0) for item in external_hazards),
            default=0.0,
        )
        data_source = external_hazards[0].source
    else:
        inside_hazard = False
        severity = 0.0
        data_source = "NO_HAZARD_DATA"

    rules = evaluate(
        inside_hazard=inside_hazard,
        severity=severity,
        incident_count=len(incidents),
    )

    confidence = 0.8 if inside_hazard else 0.45
    score = final_score(rules.score, confidence)

    factors = {
        "data_source": data_source,
        "explanations": rules.factors,
        "nearby_incident_count": len(incidents),
    }

    if external_hazards and not persisted_hazards:
        factors["hazard_mode"] = "DEMO_DATA"

    assessment = RiskAssessment(
        user_id=user.id,
        latitude=payload.latitude,
        longitude=payload.longitude,
        geom=point_wkt(payload.latitude, payload.longitude),
        risk_score=score,
        risk_level=level(score),
        model_version="rules_v1",
        confidence=confidence,
        factors=factors,
    )

    session.add(assessment)
    await session.flush()

    return RiskHistoryResponse.model_validate(assessment)


@router.get(
    "/history",
    response_model=list[RiskHistoryResponse],
    summary="List personal risk history",
)
async def history(
    user: Annotated[User, Depends(get_current_user)],
    session: Annotated[AsyncSession, Depends(get_db_session)],
    limit: int = 50,
) -> list[RiskHistoryResponse]:
    rows = (
        await session.scalars(
            select(RiskAssessment)
            .where(RiskAssessment.user_id == user.id)
            .order_by(RiskAssessment.created_at.desc())
            .limit(min(max(limit, 1), 100))
        )
    ).all()

    return [RiskHistoryResponse.model_validate(item) for item in rows]