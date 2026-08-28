# ruff: noqa: E501
"""Authenticated device registration resource."""

from datetime import UTC, datetime
from typing import Annotated

from app.api.deps import get_current_user
from app.db.models.user import User
from app.db.models.user_device import UserDevice
from app.db.session import get_db_session
from app.schemas.devices import DeviceRegisterRequest, DeviceResponse
from fastapi import APIRouter, Depends, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

router = APIRouter(prefix="/devices", tags=["Devices"])


@router.post(
    "/register",
    response_model=DeviceResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Register or update a device",
)
async def register_device(
    payload: DeviceRegisterRequest,
    user: Annotated[User, Depends(get_current_user)],
    session: Annotated[AsyncSession, Depends(get_db_session)],
) -> DeviceResponse:
    """Upsert a device identifier for future notification delivery without logging its FCM token."""
    device = await session.scalar(
        select(UserDevice).where(
            UserDevice.user_id == user.id, UserDevice.device_id == payload.device_id
        )
    )
    if device is None:
        device = UserDevice(
            user_id=user.id,
            device_id=payload.device_id,
            fcm_token=payload.fcm_token,
            platform=payload.platform,
            last_seen=datetime.now(UTC),
        )
        session.add(device)
    else:
        device.fcm_token = payload.fcm_token
        device.platform = payload.platform
        device.last_seen = datetime.now(UTC)
    await session.flush()
    return DeviceResponse.model_validate(device)
