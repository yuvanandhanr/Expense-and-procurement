from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from src.database.dependency import get_db_session
from src.auth.dependencies import RoleChecker
from src.services.dashboard_service import DashboardService

router = APIRouter(prefix="/analytics", tags=["analytics"])

# RBAC protection: Only CEO, CFO, Finance, Finance Manager, Admin, or Procurement roles can view analytics
rbac_dependency = Depends(RoleChecker(["CEO", "CFO", "Finance", "Finance Manager", "Admin", "Procurement"]))


@router.get("/spend", dependencies=[rbac_dependency])
async def get_spend_analytics(db: AsyncSession = Depends(get_db_session)):
    """
    Retrieves global spending analytics aggregated by department, vendor, category, and month.
    """
    dashboard_service = DashboardService(db)
    data = await dashboard_service.get_spend_analytics()
    return data


@router.get("/vendors", dependencies=[rbac_dependency])
async def get_vendor_analytics(db: AsyncSession = Depends(get_db_session)):
    """
    Retrieves vendor performance and historical spend analytics.
    """
    dashboard_service = DashboardService(db)
    data = await dashboard_service.get_vendor_analytics()
    return data


@router.get("/budgets", dependencies=[rbac_dependency])
async def get_budget_analytics(db: AsyncSession = Depends(get_db_session)):
    """
    Retrieves department budget utilization and consumption rate analytics.
    """
    dashboard_service = DashboardService(db)
    data = await dashboard_service.get_budget_analytics()
    return data
