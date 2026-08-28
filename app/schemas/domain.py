"""Read-only API contracts for persisted disaster-domain entities."""

from datetime import datetime
from typing import Any
from uuid import UUID

from app.db.types import Severity, ShelterStatus
from pydantic import BaseModel, ConfigDict


class HazardResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: UUID
    hazard_type: str
    severity: Severity
    confidence: float
    source: str
    valid_from: datetime
    valid_until: datetime | None
    metadata: dict[str, Any]


class ShelterResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: UUID
    name: str
    capacity: int
    current_occupancy: int
    status: ShelterStatus
    latitude: float
    longitude: float
    facilities: dict[str, Any]
    contact_information: dict[str, Any]


class ShelterNearbyResponse(ShelterResponse):
    distance_metres: float


class IncidentResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: UUID
    incident_type: str
    severity: Severity
    description: str | None
    latitude: float
    longitude: float
    source: str
    reported_at: datetime
    resolved_at: datetime | None


class WeatherObservationResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    source: str
    latitude: float
    longitude: float
    rainfall_mm: float | None
    temperature: float | None
    wind_speed: float | None
    humidity: float | None
    pressure: float | None
    observed_at: datetime
