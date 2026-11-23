"""
Database Connection Setup.

Configures the SQLAlchemy asynchronous database engine with enterprise connection pooling.
"""

from sqlalchemy.ext.asyncio import create_async_engine
from src.core.config import settings

engine_kwargs = {
    "echo": False
}

if "sqlite" not in settings.DATABASE_URL.lower():
    engine_kwargs.update({
        "pool_size": 2,             # Conservative pool size for 15-connection Supabase pooler limit
        "max_overflow": 1,          # Maximum 3 connections per instance
        "pool_timeout": 30,         # Wait up to 30s before timing out
        "pool_pre_ping": True,      # Verify connection is alive before lease
        "pool_recycle": 60,         # Recycle connections every 60 seconds
    })

# Initialize asynchronous engine targeting PostgreSQL (Supabase/local) or SQLite
async_engine = create_async_engine(
    url=settings.DATABASE_URL,
    **engine_kwargs
)

