"""Explicit demo disaster provider for local development and demonstrations."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from typing import Any

from app.db.types import Severity
from app.integrations.disaster.base import NormalizedHazard, ProviderResult


class DemoDisasterProvider:
    """Provides clearly marked demo hazards."""

    @property
    def name(self) -> str:
        return "DEMO_DATA"

    async def fetch(
        self,
        *,
        latitude: float,
        longitude: float,
        radius_km: float,
    ) -> ProviderResult:
        """Return deterministic demo hazards around the requested point."""

        now = datetime.now(UTC)

        # Small square around the requested point.
        delta = 0.01

        polygon = {
            "type": "Polygon",
            "coordinates": [
                [
                    [longitude - delta, latitude - delta],
                    [longitude + delta, latitude - delta],
                    [longitude + delta, latitude + delta],
                    [longitude - delta, latitude + delta],
                    [longitude - delta, latitude - delta],
                ]
            ],
        }

        hazard = NormalizedHazard(
            hazard_type="flood",
            severity=Severity.HIGH,
            confidence=0.85,
            source=self.name,
            valid_from=now - timedelta(minutes=30),
            valid_until=now + timedelta(hours=2),
            geometry=polygon,
            metadata={
                "data_mode": "DEMO DATA",
                "provider": self.name,
                "description": "Demonstration flood hazard only.",
                "radius_km": radius_km,
            },
        )

        return ProviderResult(
            hazards=(hazard,),
            source=self.name,
            observed_at=now,
            received_at=now,
            is_stale=False,
        )


__all__ = ["DemoDisasterProvider"]