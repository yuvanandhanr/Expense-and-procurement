"""
Application Entrypoint.

Initializes the FastAPI application, registers custom middlewares, registers routes,
and manages application startup/shutdown lifespans.
"""

import logging
from contextlib import asynccontextmanager
from fastapi import Depends, FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.config import settings
from src.core.logging_config import setup_logging
from src.database.database import async_engine
from src.database.dependency import get_db_session
from src.middleware.exceptions import ExceptionMiddleware
from src.middleware.logging import LoggingMiddleware
from src.middleware.request_id import RequestIdMiddleware
from src.middleware.security import SecurityHeadersMiddleware

logger = logging.getLogger("api.main")


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Lifespan context manager managing database connections and logging lifecycles.
    """
    # 1. Initialize logging configuration
    setup_logging()
    logger.info("Initializing FastAPI Application Lifespan...")

    # 2. Verify connection to the PostgreSQL database
    try:
        async with async_engine.connect() as conn:
            await conn.execute(select(1))
        logger.info("Database connection verified successfully on startup.")
    except Exception as exc:
        logger.critical(
            "CRITICAL: Database connection check failed on startup. Server is degraded: %s",
            str(exc)
        )
        # Avoid crashing startup so the health-check system can report failure properly

    yield

    # 3. Clean up database connections on application termination
    logger.info("Terminating FastAPI Application. Disposing database engine...")
    await async_engine.dispose()
    logger.info("Database engine disposed.")


app = FastAPI(
    title="Enterprise Expense & Procurement Workflow Platform API",
    description="Production-ready project foundation and skeleton for expense tracking and procurement workflows.",
    version=settings.APP_VERSION,
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc"
)

# Apply middlewares (executed in reverse order of addition)
app.add_middleware(ExceptionMiddleware)
app.add_middleware(LoggingMiddleware)
app.add_middleware(RequestIdMiddleware)
app.add_middleware(SecurityHeadersMiddleware)
app.add_middleware(GZipMiddleware, minimum_size=1000)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Adjust for production configurations
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.add_middleware(
    TrustedHostMiddleware,
    allowed_hosts=["*"] if settings.ENVIRONMENT != "production" else ["localhost", "127.0.0.1"]
)


@app.get("/", tags=["system"])
async def get_root():
    """
    Welcome endpoint returning basic api versioning and status info.
    """
    return {
        "message": "Welcome to the Enterprise Expense & Procurement Workflow Platform API",
        "version": settings.APP_VERSION,
        "environment": settings.ENVIRONMENT
    }


@app.get("/health", tags=["system"])
async def get_health():
    """
    Liveness probe returning HTTP 200 to confirm application process is running.
    """
    return {
        "status": "healthy"
    }


@app.get("/ready", tags=["system"])
async def get_readiness(db: AsyncSession = Depends(get_db_session)):
    """
    Readiness probe to verify database connectivity.
    """
    try:
        # Run standard select 1 to check DB connection status
        await db.execute(select(1))
        return {
            "status": "ready",
            "database": "connected"
        }
    except Exception as exc:
        logger.error("Readiness check failed: Database connection issue: %s", str(exc))
        raise HTTPException(
            status_code=503,
            detail="Database connection is offline"
        )


@app.get("/version", tags=["system"])
async def get_version():
    """
    Returns the semantic version of the application.
    """
    return {
        "version": settings.APP_VERSION
    }
