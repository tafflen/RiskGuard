"""Optional async Redis capability; all callers must tolerate unavailable Redis."""

import json
import logging
from functools import lru_cache
from typing import cast

from redis.asyncio import Redis, from_url
from redis.exceptions import RedisError

from app.core.config import Settings, get_settings

LOGGER = logging.getLogger(__name__)


class RedisClient:
    """Best-effort cache/state interface that returns misses rather than application errors."""

    def __init__(self, client: Redis) -> None:
        self._client = client

    async def get_json(self, key: str) -> object | None:
        try:
            value = await self._client.get(key)
            return json.loads(value) if value is not None else None
        except (RedisError, json.JSONDecodeError):
            LOGGER.warning("Redis cache read unavailable")
            return None

    async def set_json(self, key: str, value: object, ttl_seconds: int) -> bool:
        try:
            await self._client.set(key, json.dumps(value, separators=(",", ":")), ex=ttl_seconds)
            return True
        except (RedisError, TypeError):
            LOGGER.warning("Redis cache write unavailable")
            return False

    async def check_fixed_window(self, key: str, limit: int, window_seconds: int) -> bool:
        """Return true if allowed; fail open when Redis cannot be reached."""
        try:
            count = cast(int, await self._client.incr(key))
            if count == 1:
                await self._client.expire(key, window_seconds)
            return count <= limit
        except RedisError:
            LOGGER.warning("Redis rate limiting unavailable")
            return True

    async def health(self) -> bool:
        try:
            return cast(bool, await self._client.ping())
        except RedisError:
            return False

    async def close(self) -> None:
        await self._client.aclose()


def build_redis(settings: Settings) -> RedisClient:
    client = cast(Redis, from_url(settings.redis_url, encoding="utf-8", decode_responses=True))  # type: ignore[no-untyped-call]
    return RedisClient(client)


@lru_cache
def get_redis() -> RedisClient:
    return build_redis(get_settings())


async def close_redis() -> None:
    await get_redis().close()
    get_redis.cache_clear()
