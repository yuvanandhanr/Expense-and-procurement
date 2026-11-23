from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from src.database.dependency import get_db_session
from src.auth.dependencies import RoleChecker, get_current_user
from src.models.auth import User
from src.services.dashboard_service import DashboardService

router = APIRouter(prefix="/analytics", tags=["analytics"])

# RBAC protection: Only CEO, CFO, Finance, Finance Manager, Admin, or Procurement roles can view global analytics
rbac_dependency = Depends(RoleChecker(["CEO", "CFO", "Finance", "Finance Manager", "Admin", "Procurement"]))


@router.get("/spend", dependencies=[rbac_dependency])
async def get_spend_legacy(timeframe: str = "all", db: AsyncSession = Depends(get_db_session)):
    dashboard_service = DashboardService(db)
    return await dashboard_service.get_spend_analytics(timeframe=timeframe)


@router.get("/spending")
async def get_spend_analytics(
    timeframe: str = "all",
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session)
):
    """
    Retrieves spending analytics. Elevated roles see global metrics; employees see only their own expense data.
    """
    user_roles = {role.role_name for role in current_user.roles if role.status}
    is_elevated = bool(user_roles & {"CEO", "CFO", "Finance", "Finance Manager", "Admin", "Procurement"})

    dashboard_service = DashboardService(db)
    if is_elevated:
        return await dashboard_service.get_spend_analytics(timeframe=timeframe)
    else:
        return await dashboard_service.get_employee_spend_analytics(user_id=current_user.user_id, timeframe=timeframe)



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
