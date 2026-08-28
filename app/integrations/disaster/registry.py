"""Registry for configured disaster-data providers."""

from __future__ import annotations

from collections.abc import Iterable

from app.integrations.disaster.base import DisasterProvider


class DisasterProviderRegistry:
    """Stores and retrieves configured disaster-data providers."""

    def __init__(self, providers: Iterable[DisasterProvider] = ()) -> None:
        self._providers: dict[str, DisasterProvider] = {}

        for provider in providers:
            self.register(provider)

    def register(self, provider: DisasterProvider) -> None:
        """Register a provider by its stable name."""
        name = provider.name.strip()

        if not name:
            raise ValueError("Disaster provider name must not be empty")

        if name in self._providers:
            raise ValueError(f"Disaster provider already registered: {name}")

        self._providers[name] = provider

    def get(self, name: str) -> DisasterProvider | None:
        """Return a provider by name, if registered."""
        return self._providers.get(name)

    def all(self) -> tuple[DisasterProvider, ...]:
        """Return all registered providers."""
        return tuple(self._providers.values())

    def is_empty(self) -> bool:
        """Return whether no providers are configured."""
        return not self._providers