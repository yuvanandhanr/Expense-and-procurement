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
    role_name = "Employee"
    for r in current_user.roles:
        if r.status:
            role_name = r.role_name
            break

    dashboard_service = DashboardService(db)
    data = await dashboard_service.get_dashboard_data(role_name, current_user.user_id)
    return data
