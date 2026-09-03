"""
Database Connection Setup.

Configures the SQLAlchemy asynchronous database engine with enterprise connection pooling.
"""

from sqlalchemy.ext.asyncio import create_async_engine
from src.core.config import settings

# Initialize asynchronous engine targeting Supabase PostgreSQL with strict pool constraints
async_engine = create_async_engine(
    url=settings.DATABASE_URL,
    pool_size=4,             # Maintain up to 4 connections in pool
    max_overflow=2,          # Allow temporary overflow up to 2 additional connections
    pool_timeout=20,         # Timeout after 20s if all connections busy
    pool_pre_ping=True,      # Verify connection is alive before lease
    pool_recycle=300,        # Recycle connection after 5 minutes
    echo=False               # Query statement logging managed via LOG_LEVEL
)
