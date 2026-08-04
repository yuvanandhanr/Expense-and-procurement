import pickle
import logging
from typing import Any, Optional
import redis.asyncio as redis
from src.cache.base import BaseCache

logger = logging.getLogger(__name__)


class RedisCache(BaseCache):
    """
    Redis cache implementation with automatic serialization.
    """

    def __init__(self, redis_url: str) -> None:
        self.redis_url = redis_url
        self.client = redis.from_url(redis_url)

    async def get(self, key: str) -> Optional[Any]:
        try:
            data = await self.client.get(key)
            if data is None:
                return None
            return pickle.loads(data)
        except Exception as e:
            logger.error(f"Redis get failed for key '{key}': {e}")
            return None

    async def set(self, key: str, value: Any, expire_seconds: Optional[int] = None) -> None:
        try:
            serialized = pickle.dumps(value)
            if expire_seconds:
                await self.client.setex(key, expire_seconds, serialized)
            else:
                await self.client.set(key, serialized)
        except Exception as e:
            logger.error(f"Redis set failed for key '{key}': {e}")

    async def delete(self, key: str) -> None:
        try:
            await self.client.delete(key)
        except Exception as e:
            logger.error(f"Redis delete failed for key '{key}': {e}")

    async def clear(self) -> None:
        try:
            await self.client.flushdb()
        except Exception as e:
            logger.error(f"Redis flushdb failed: {e}")
