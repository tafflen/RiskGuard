"""Provider contracts and normalized data types for disaster information."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Protocol

from app.db.types import Severity


@dataclass(frozen=True, slots=True)
class NormalizedHazard:
    """Provider-independent representation of a disaster hazard."""

    hazard_type: str
    severity: Severity
    confidence: float
    source: str
    valid_from: datetime
    valid_until: datetime | None
    geometry: Any
    metadata: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not self.hazard_type.strip():
            raise ValueError("hazard_type must not be empty")

        if not self.source.strip():
            raise ValueError("source must not be empty")

        if not 0.0 <= self.confidence <= 1.0:
            raise ValueError("confidence must be between 0 and 1")

        if self.valid_until is not None and self.valid_until < self.valid_from:
            raise ValueError("valid_until must be greater than or equal to valid_from")


@dataclass(frozen=True, slots=True)
class ProviderResult:
    """Normalized result returned by a disaster-data provider."""

    hazards: tuple[NormalizedHazard, ...]
    source: str
    observed_at: datetime | None = None
    received_at: datetime | None = None
    is_stale: bool = False


class DisasterProviderError(Exception):
    """Base exception for disaster-provider failures."""


class DisasterProviderUnavailable(DisasterProviderError):
    """Raised when a configured provider cannot currently be reached."""


class DisasterProviderResponseError(DisasterProviderError):
    """Raised when a provider response cannot be safely normalized."""


class DisasterProvider(Protocol):
    """Contract implemented by every external disaster-data provider."""

    @property
    def name(self) -> str:
        """Return the stable provider name."""

    async def fetch(
        self,
        *,
        latitude: float,
        longitude: float,
        radius_km: float,
    ) -> ProviderResult:
        """Fetch and normalize hazards around a geographic point."""