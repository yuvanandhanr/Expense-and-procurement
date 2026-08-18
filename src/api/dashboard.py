from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from src.database.dependency import get_db_session
from src.auth.dependencies import get_current_user
from src.models.auth import User
from src.services.dashboard_service import DashboardService

router = APIRouter(tags=["dashboard"])


@router.get("/dashboard")
async def get_dashboard(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session)
):
    """
    Returns dashboard metrics tailored to the current user's role.
    """
    # Default to "Employee" if roles is empty or status is disabled
    role_priority = {
        "CEO": 100,
        "Admin": 90,
        "CFO": 80,
        "Finance Manager": 70,
        "Finance": 60,
        "Procurement": 50,
        "Manager": 40,
        "Vendor": 30,
        "Vendor Portal": 20,
        "Employee": 10
    }

    active_roles = [r.role_name for r in current_user.roles if r.status]
    if active_roles:
        active_roles.sort(key=lambda x: role_priority.get(x, 0), reverse=True)
        role_name = active_roles[0]
    else:
        role_name = "Employee"

    dashboard_service = DashboardService(db)
    data = await dashboard_service.get_dashboard_data(role_name, current_user.user_id)
    # inject debug
    data["debug_active_roles"] = active_roles
    return data
