"""
Database Session Dependency.

Exposes an asynchronous generator function designed for FastAPI dependency injection,
managing session scopes, commits, rollbacks, and teardown.
"""

from typing import AsyncGenerator
from sqlalchemy.ext.asyncio import AsyncSession
from src.database.session import async_session


async def get_db_session() -> AsyncGenerator[AsyncSession, None]:
    """
    Yields an AsyncSession scope for a request transaction.
    
    Performs automatic rollback on unhandled exceptions and commits on success.
    """
    async with async_session() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()
