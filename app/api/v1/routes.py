# ruff: noqa: E501
"""Safe-routing capability boundary until a verified routing provider is configured."""

from typing import Annotated

from app.api.deps import get_current_user
from app.core.exceptions import RiskGuardError
from app.db.models.user import User
from app.schemas.geospatial import Coordinate
from fastapi import APIRouter, Depends
from pydantic import BaseModel, ConfigDict

router = APIRouter(prefix="/routes", tags=["Routes"])


class SafeRouteRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    origin: Coordinate
    destination: Coordinate


@router.post("/safe", summary="Request a risk-aware safe route")
async def safe_route(_: SafeRouteRequest, __: Annotated[User, Depends(get_current_user)]) -> None:
    raise RiskGuardError(
        "ROUTING_UNAVAILABLE",
        "Safe routing is not available until a routing provider is configured.",
        503,
    )
