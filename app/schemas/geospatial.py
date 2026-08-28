"""Shared coordinate and list-query contracts."""

from pydantic import BaseModel, ConfigDict, Field


class Coordinate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    latitude: float = Field(ge=-90, le=90)
    longitude: float = Field(ge=-180, le=180)


class RadiusQuery(Coordinate):
    radius_metres: float = Field(default=5_000, gt=0, le=50_000)
    limit: int = Field(default=20, ge=1, le=100)
