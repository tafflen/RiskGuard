"""Device registration contracts. FCM delivery is implemented in a later phase."""

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class DeviceRegisterRequest(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True, extra="forbid")

    device_id: str = Field(min_length=1, max_length=255)
    fcm_token: str | None = Field(default=None, min_length=1, max_length=4_096)
    platform: str = Field(min_length=1, max_length=32)


class DeviceResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    device_id: str
    platform: str
    last_seen: datetime | None
