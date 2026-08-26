"""
Application Entrypoint.

Initializes the FastAPI application, registers custom middlewares, registers routes,
and manages application startup/shutdown lifespans.
"""

import logging
from contextlib import asynccontextmanager
from fastapi import Depends, FastAPI, HTTPException
from fastapi.staticfiles import StaticFiles
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
from src.api.auth import router as auth_router
from src.api.users import router as users_router
from src.api.roles import router as roles_router
from src.api.permissions import router as permissions_router
from src.api.departments import router as departments_router
from src.api.designations import router as designations_router
from src.api.cost_centres import router as cost_centres_router
from src.api.budget_codes import router as budget_codes_router
from src.api.organization import router as org_router
from src.api.purchase_requisitions import router as pr_router
from src.api.approvals import router as approvals_router
from src.api.approvals_inbox import router as approvals_inbox_router
from src.api.comments import router as comments_router
from src.api.attachments import router as attachments_router
from src.api.vendors import router as vendors_router
from src.api.rfq import router as rfq_router
from src.api.quotations import router as quotations_router
from src.api.purchase_orders import router as purchase_orders_router
from src.api.contracts import router as contracts_router
from src.api.assets import router as assets_router
from src.api.asset_incidents import router as asset_incidents_router
from src.api.deliveries import router as deliveries_router
from src.api.grn import router as grn_router
from src.api.offboarding import router as offboarding_router

# Phase 6 imports
from src.api.dashboard import router as dashboard_router
from src.api.analytics import router as analytics_router
from src.api.reports import router as reports_router
from src.api.notifications import router as notifications_router
from src.api.audit import router as audit_router
from src.api.search import router as search_router
from src.api.files import router as files_router
from src.api.monitoring import router as monitoring_router
from src.api.settings import router as settings_router

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

    # 2.5 Initialize Cache, Seed Databases, and Start Background Scheduler
    import asyncio
    from src.cache.factory import initialize_cache
    from src.database.session import async_session
    from src.services.setting_service import SettingService
    from src.services.email_service import EmailService
    from src.services.notification_service import NotificationService
    from src.services.job_service import run_scheduler_loop

    await initialize_cache()

    try:
        async with async_session() as session:
            # Seed Settings
            setting_service = SettingService(session)
            await setting_service.seed_default_settings()

            # Seed Email Templates
            email_service = EmailService(session)
            await email_service.seed_templates()

            # Seed Notification Templates
            notification_service = NotificationService(session)
            await notification_service.seed_templates()

            await session.commit()
        logger.info("Successfully seeded settings, email templates, and notification templates on startup.")
    except Exception as e:
        logger.error(f"Error seeding default settings/templates on startup: {e}")

    # Launch background scheduler task
    scheduler_task = asyncio.create_task(run_scheduler_loop(async_session))
    app.state.scheduler_task = scheduler_task

    yield

    # 3. Clean up database connections on application termination
    logger.info("Terminating FastAPI Application. Disposing database engine...")
    if hasattr(app.state, "scheduler_task"):
        logger.info("Cancelling background scheduler task...")
        app.state.scheduler_task.cancel()
        try:
            await app.state.scheduler_task
        except asyncio.CancelledError:
            pass
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

# Include Authentication and Authorization routes
app.include_router(auth_router, prefix="/api/v1")
app.include_router(users_router, prefix="/api/v1")
app.include_router(roles_router, prefix="/api/v1")
app.include_router(permissions_router, prefix="/api/v1")
app.include_router(departments_router, prefix="/api/v1/departments")
app.include_router(designations_router, prefix="/api/v1/designations")
app.include_router(cost_centres_router, prefix="/api/v1/cost_centres")
app.include_router(budget_codes_router, prefix="/api/v1/budget_codes")
app.include_router(org_router, prefix="/api/v1/settings")
app.include_router(pr_router, prefix="/api/v1")
app.include_router(approvals_router, prefix="/api/v1")
app.include_router(approvals_inbox_router, prefix="/api/v1")
app.include_router(comments_router, prefix="/api/v1")
app.include_router(attachments_router, prefix="/api/v1")
app.include_router(vendors_router, prefix="/api/v1")
app.include_router(rfq_router, prefix="/api/v1")
app.include_router(quotations_router, prefix="/api/v1")
app.include_router(purchase_orders_router, prefix="/api/v1")
app.include_router(contracts_router, prefix="/api/v1")
app.include_router(assets_router, prefix="/api/v1")
app.include_router(asset_incidents_router, prefix="/api/v1")
app.include_router(deliveries_router, prefix="/api/v1")
app.include_router(grn_router, prefix="/api/v1")
app.include_router(offboarding_router, prefix="/api/v1")

from src.api.invoices import router as invoices_router
from src.api.expenses import router as expenses_router

# Mount Phase 6 routers
app.include_router(dashboard_router, prefix="/api/v1")
app.include_router(analytics_router, prefix="/api/v1")
app.include_router(reports_router, prefix="/api/v1")
app.include_router(notifications_router, prefix="/api/v1")
app.include_router(audit_router, prefix="/api/v1")
app.include_router(search_router, prefix="/api/v1")
app.include_router(files_router, prefix="/api/v1")
app.include_router(monitoring_router, prefix="/api/v1")
app.include_router(settings_router, prefix="/api/v1")
app.include_router(invoices_router, prefix="/api/v1")
app.include_router(expenses_router, prefix="/api/v1")

# Mount Static Files for Uploads
import os
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
UPLOAD_DIR = os.path.join(BASE_DIR, "uploads")
os.makedirs(UPLOAD_DIR, exist_ok=True)
app.mount("/uploads", StaticFiles(directory=UPLOAD_DIR), name="uploads")


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
