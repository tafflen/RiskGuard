# ruff: noqa: E501
"""Verified-configured weather provider boundary; never fabricates current observations."""

from dataclasses import dataclass
from datetime import UTC, datetime

import httpx

from app.core.config import Settings


class WeatherProviderError(RuntimeError):
    """Safe external-provider failure that callers can degrade around."""


@dataclass(frozen=True, slots=True)
class WeatherReading:
    source: str
    latitude: float
    longitude: float
    observed_at: datetime
    received_at: datetime
    confidence: float
    rainfall_mm: float | None = None
    temperature: float | None = None
    wind_speed: float | None = None
    humidity: float | None = None
    pressure: float | None = None


class WeatherProvider:
    """Provider protocol implemented by real adapters; no client input can control its URL."""

    async def current(self, latitude: float, longitude: float) -> WeatherReading:
        raise NotImplementedError


class ConfiguredWeatherProvider(WeatherProvider):
    """Provider adapter requiring an explicitly configured, documented upstream endpoint."""

    def __init__(self, settings: Settings, client: httpx.AsyncClient) -> None:
        if settings.weather_base_url is None or settings.weather_api_key is None:
            raise WeatherProviderError("Weather provider is not configured.")
        self._base_url = settings.weather_base_url
        self._key = settings.weather_api_key.get_secret_value()
        self._client = client
        self._timeout = settings.external_request_timeout_seconds
        self._attempts = settings.external_request_max_attempts

    async def current(self, latitude: float, longitude: float) -> WeatherReading:
        """Fetch a provider response; normalization is intentionally provider-specific and validated."""
        last_error: Exception | None = None
        for attempt in range(self._attempts):
            try:
                response = await self._client.get(
                    self._base_url,
                    params={"lat": latitude, "lon": longitude},
                    headers={"Authorization": f"Bearer {self._key}"},
                    timeout=self._timeout,
                )
                response.raise_for_status()
                payload = response.json()
                return self._normalize(payload, latitude, longitude)
            except (httpx.HTTPError, ValueError, KeyError, TypeError) as exc:
                last_error = exc
                if attempt + 1 < self._attempts:
                    import asyncio

                    await asyncio.sleep(2**attempt)
        raise WeatherProviderError("Weather provider request failed.") from last_error

    @staticmethod
    def _normalize(payload: object, latitude: float, longitude: float) -> WeatherReading:
        """Reject undocumented payloads rather than guessing field meanings."""
        if not isinstance(payload, dict) or not isinstance(payload.get("observed_at"), str):
            raise WeatherProviderError(
                "Weather provider response has no supported normalized contract."
            )
        observed_at = datetime.fromisoformat(payload["observed_at"].replace("Z", "+00:00"))
        return WeatherReading(
            source=str(payload.get("source", "configured_weather_provider")),
            latitude=latitude,
            longitude=longitude,
            observed_at=observed_at.astimezone(UTC),
            received_at=datetime.now(UTC),
            confidence=float(payload.get("confidence", 0.5)),
            rainfall_mm=_number(payload.get("rainfall_mm")),
            temperature=_number(payload.get("temperature")),
            wind_speed=_number(payload.get("wind_speed")),
            humidity=_number(payload.get("humidity")),
            pressure=_number(payload.get("pressure")),
        )


def _number(value: object) -> float | None:
    return float(value) if isinstance(value, int | float) else None
