"""Factory for creating the configured disaster-data service."""

from __future__ import annotations

from app.integrations.disaster.mock import DemoDisasterProvider
from app.integrations.disaster.registry import DisasterProviderRegistry
from app.integrations.disaster.service import DisasterService


def create_disaster_service() -> DisasterService:
    """Create the disaster service for the current environment.

    Demo data is intentionally explicit and can later be replaced with
    real external providers without changing the service contract.
    """

    registry = DisasterProviderRegistry(
        providers=[
            DemoDisasterProvider(),
        ]
    )

    return DisasterService(registry)


disaster_service = create_disaster_service()


__all__ = ["create_disaster_service", "disaster_service"]