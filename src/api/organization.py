from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from src.auth.dependencies import PermissionChecker, get_current_user
from src.database.dependency import get_db_session
from src.models.auth import User
from src.schemas.organization import OrgSettingsSchema, OrgSettingsUpdate
from src.services.organization_service import OrgSettingsService

router = APIRouter(tags=["Organization Settings"])


@router.get("", response_model=OrgSettingsSchema)
async def get_settings(
    db: AsyncSession = Depends(get_db_session),
    current_user: User = Depends(get_current_user)
):
    """
    Retrieves the organization configuration settings.
    """
    service = OrgSettingsService(db)
    return await service.get_settings()


@router.put("", response_model=OrgSettingsSchema)
async def update_settings(
    data: OrgSettingsUpdate,
    db: AsyncSession = Depends(get_db_session),
    current_user: User = Depends(PermissionChecker("admin.settings"))
):
    """
    Updates the organization configuration settings.
    """
    service = OrgSettingsService(db)
    return await service.update_settings(data)
