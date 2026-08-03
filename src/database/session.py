"""
Database Session Configuration.

Defines the asynchronous session factory bound to the async engine.
"""

from sqlalchemy.ext.asyncio import async_sessionmaker
from src.database.database import async_engine

# Asynchronous session factory configured for non-expiring commits on reload
async_session = async_sessionmaker(
    bind=async_engine,
    autoflush=False,
    autocommit=False,
    expire_on_commit=False
)
