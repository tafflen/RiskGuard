# ruff: noqa: E501
"""Alert-read capability boundary; alert persistence and FCM are later phases."""

from typing import Annotated

from app.api.deps import get_current_user
from app.core.exceptions import RiskGuardError
from app.db.models.user import User
from fastapi import APIRouter, Depends

router = APIRouter(prefix="/alerts", tags=["Alerts"])


@router.get("", summary="List alerts for the current user")
async def list_alerts(_: Annotated[User, Depends(get_current_user)]) -> None:
    raise RiskGuardError(
        "ALERTS_UNAVAILABLE",
        "Alerts are not available until notification delivery is configured.",
        503,
    )
