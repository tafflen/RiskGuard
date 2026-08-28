"""Service layer for collecting disaster information from configured providers."""

from __future__ import annotations

from app.integrations.disaster.base import (
    DisasterProvider,
    DisasterProviderError,
    NormalizedHazard,
    ProviderResult,
)
from app.integrations.disaster.registry import DisasterProviderRegistry


class DisasterService:
    """Coordinates configured disaster providers without fabricating data."""

    def __init__(self, registry: DisasterProviderRegistry) -> None:
        self.registry = registry

    async def fetch_nearby(
        self,
        *,
        latitude: float,
        longitude: float,
        radius_km: float = 25.0,
    ) -> tuple[NormalizedHazard, ...]:
        """Fetch hazards from every configured provider."""

        self._validate_coordinates(latitude, longitude)

        if not 0 < radius_km <= 500:
            raise ValueError("radius_km must be greater than 0 and at most 500")

        hazards: list[NormalizedHazard] = []

        for provider in self.registry.all():
            try:
                result: ProviderResult = await provider.fetch(
                    latitude=latitude,
                    longitude=longitude,
                    radius_km=radius_km,
                )
            except DisasterProviderError:
                # A failed provider must not create fake hazard data.
                continue

            hazards.extend(result.hazards)

        return tuple(hazards)

    @staticmethod
    def _validate_coordinates(latitude: float, longitude: float) -> None:
        """Validate geographic coordinates before provider calls."""

        if not -90 <= latitude <= 90:
            raise ValueError("latitude must be between -90 and 90")

        if not -180 <= longitude <= 180:
            raise ValueError("longitude must be between -180 and 180")


__all__ = ["DisasterService"]