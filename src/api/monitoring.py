from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from src.database.dependency import get_db_session
from src.auth.dependencies import get_current_user
from src.services.monitoring_service import MonitoringService

router = APIRouter(prefix="/system", tags=["monitoring"])


@router.get("/health")
async def get_system_health(
    current_user = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session)
):
    """
    Checks component health states (Database, Storage, Cache, Queue, Scheduler).
    """
    service = MonitoringService(db)
    health_status = await service.perform_system_health_check()
    return health_status


@router.get("/metrics")
async def get_system_metrics(
    current_user = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session)
):
    """
    Retrieves system performance metrics (CPU, RAM, API latencies).
    """
    service = MonitoringService(db)
    metrics = await service.collect_system_metrics()
    return metrics
