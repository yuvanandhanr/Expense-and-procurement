from typing import Any, Optional


class BaseCache:
    """
    Abstract Base Cache Interface.
    """

    async def get(self, key: str) -> Optional[Any]:
        """
        Retrieve a value from the cache.
        """
        raise NotImplementedError

    async def set(self, key: str, value: Any, expire_seconds: Optional[int] = None) -> None:
        """
        Store a value in the cache with an optional expiration time.
        """
        raise NotImplementedError

    async def delete(self, key: str) -> None:
        """
        Delete a key from the cache.
        """
        raise NotImplementedError

    async def clear(self) -> None:
        """
        Clear all keys from the cache.
        """
        raise NotImplementedError
