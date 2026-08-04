import time
from typing import Any, Dict, Optional, Tuple
from src.cache.base import BaseCache


class MemoryCache(BaseCache):
    """
    In-memory dictionary cache implementation with key expiration.
    """

    def __init__(self) -> None:
        # Structure: key -> (value, expire_at_timestamp_or_none)
        self._store: Dict[str, Tuple[Any, Optional[float]]] = {}

    async def get(self, key: str) -> Optional[Any]:
        if key not in self._store:
            return None

        val, expire_at = self._store[key]
        if expire_at is not None and time.time() > expire_at:
            # Expired, clean up
            del self._store[key]
            return None

        return val

    async def set(self, key: str, value: Any, expire_seconds: Optional[int] = None) -> None:
        expire_at = None
        if expire_seconds is not None:
            expire_at = time.time() + expire_seconds
        self._store[key] = (value, expire_at)

    async def delete(self, key: str) -> None:
        if key in self._store:
            del self._store[key]

    async def clear(self) -> None:
        self._store.clear()
