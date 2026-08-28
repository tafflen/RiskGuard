"""Minimal Phase 4 risk API contracts; scoring arrives with the risk engine."""

from datetime import datetime
from typing import Any
from uuid import UUID

from app.db.types import RiskLevel
from app.schemas.geospatial import Coordinate
from pydantic import BaseModel, ConfigDict


class RiskAssessRequest(Coordinate):
    pass


class RiskHistoryResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    latitude: float
    longitude: float
    risk_score: float
    risk_level: RiskLevel
    model_version: str
    confidence: float
    factors: dict[str, Any]
    created_at: datetime
