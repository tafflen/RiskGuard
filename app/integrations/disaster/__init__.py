"""Disaster-data provider integrations."""

from app.integrations.disaster.base import (
    DisasterProvider,
    DisasterProviderError,
    DisasterProviderResponseError,
    DisasterProviderUnavailable,
    NormalizedHazard,
    ProviderResult,
)
from app.integrations.disaster.registry import DisasterProviderRegistry

__all__ = [
    "DisasterProvider",
    "DisasterProviderError",
    "DisasterProviderResponseError",
    "DisasterProviderRegistry",
    "DisasterProviderUnavailable",
    "NormalizedHazard",
    "ProviderResult",
]