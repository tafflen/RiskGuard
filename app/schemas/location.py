"""Location API contracts that do not expose full history by default."""

from datetime import datetime
from uuid import UUID

from app.schemas.geospatial import Coordinate
from pydantic import ConfigDict, Field


class LocationCreate(Coordinate):
    accuracy: float | None = Field(default=None, ge=0, le=100_000)
    timestamp: datetime


class LocationResponse(LocationCreate):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    created_at: datetime
