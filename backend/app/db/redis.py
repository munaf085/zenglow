"""
Redis client setup and dependency injection.
"""
from typing import AsyncGenerator, Optional

import redis.asyncio as aioredis

from app.core.config import settings
from app.core.logging import get_logger

logger = get_logger(__name__)

_redis_pool: Optional[aioredis.ConnectionPool] = None


def get_redis_pool() -> aioredis.ConnectionPool:
    global _redis_pool
    if _redis_pool is None:
        _redis_pool = aioredis.ConnectionPool.from_url(
            settings.REDIS_URL,
            decode_responses=True,
            max_connections=20,
        )
    return _redis_pool


async def get_redis() -> AsyncGenerator[aioredis.Redis, None]:
    """FastAPI dependency that provides a Redis client."""
    pool = get_redis_pool()
    client = aioredis.Redis(connection_pool=pool)
    try:
        yield client
    finally:
        await client.aclose()


async def get_redis_client() -> aioredis.Redis:
    """Direct Redis client (for use in services/background tasks)."""
    pool = get_redis_pool()
    return aioredis.Redis(connection_pool=pool)
