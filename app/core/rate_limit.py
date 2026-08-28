"""Rate-limit abstractions; Redis-backed enforcement is implemented in Phase 10."""

from typing import Protocol

from app.core.redis import RedisClient


class RateLimiter(Protocol):
    """Minimal interface enabling Redis and test implementations without API coupling."""

    async def check(self, key: str, limit: int, window_seconds: int) -> bool:
        """Return whether a request is currently permitted."""


class RedisRateLimiter:
    """Redis-backed rate limiter that deliberately degrades when Redis is unavailable."""

    def __init__(self, redis: RedisClient) -> None:
        self._redis = redis

    async def check(self, key: str, limit: int, window_seconds: int) -> bool:
        return await self._redis.check_fixed_window(key, limit, window_seconds)
