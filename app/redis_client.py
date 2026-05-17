from __future__ import annotations

from functools import lru_cache

import redis.asyncio as redis

from .settings import get_settings


@lru_cache(maxsize=1)
def get_redis() -> redis.Redis:
    return redis.from_url(get_settings().redis_url, decode_responses=True)
