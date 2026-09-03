"""
Database Connection Setup.

Configures the SQLAlchemy asynchronous database engine with enterprise connection pooling.
"""

from sqlalchemy.ext.asyncio import create_async_engine
from src.core.config import settings

engine_kwargs = {
    "echo": False
}

if "sqlite" not in settings.DATABASE_URL:
    engine_kwargs.update({
        "pool_size": 20,
        "max_overflow": 10,
        "pool_pre_ping": True,
        "pool_recycle": 1800,
    })

# Initialize asynchronous engine targeting Supabase PostgreSQL or local SQLite
async_engine = create_async_engine(
    url=settings.DATABASE_URL,
    **engine_kwargs
)
