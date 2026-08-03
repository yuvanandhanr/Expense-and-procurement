"""
Database Connection Setup.

Configures the SQLAlchemy asynchronous database engine with enterprise connection pooling.
"""

from sqlalchemy.ext.asyncio import create_async_engine
from src.core.config import settings

# Initialize asynchronous engine targeting Supabase PostgreSQL
async_engine = create_async_engine(
    url=settings.DATABASE_URL,
    pool_size=20,            # Maintain up to 20 connections in pool
    max_overflow=10,         # Allow temporary overflow up to 10 additional connections
    pool_pre_ping=True,      # Verify connection is alive before lease
    pool_recycle=1800,       # Recycle connection after 30 minutes to mitigate leaks
    echo=False               # Query statement logging managed via LOG_LEVEL
)
