import logging
import asyncio
from src.core.config import settings
from src.cache.base import BaseCache
from src.cache.memory import MemoryCache
from src.cache.redis import RedisCache

logger = logging.getLogger(__name__)

# Global cache instance
_cache_instance: BaseCache = None


async def initialize_cache() -> BaseCache:
    """
    Attempts to initialize connection to Redis. If unsuccessful, falls back
    to MemoryCache.
    """
    global _cache_instance
    if _cache_instance is not None:
        return _cache_instance

    if not settings.REDIS_URL:
        logger.info("REDIS_URL not configured. Initializing MemoryCache.")
        _cache_instance = MemoryCache()
        return _cache_instance

    try:
        redis_cache = RedisCache(settings.REDIS_URL)
        # Test connection with a ping having a short timeout
        await asyncio.wait_for(redis_cache.client.ping(), timeout=2.0)
        logger.info("Redis cache connection established successfully.")
        _cache_instance = redis_cache
    except Exception as e:
        logger.warning(
            f"Failed to connect to Redis at '{settings.REDIS_URL}': {e}. "
            "Falling back to MemoryCache."
        )
        _cache_instance = MemoryCache()

    return _cache_instance


def get_cache() -> BaseCache:
    """
    Synchronous access to the initialized cache instance.
    Defaults to MemoryCache if initialize_cache has not completed yet.
    """
    global _cache_instance
    if _cache_instance is None:
        _cache_instance = MemoryCache()
    return _cache_instance
