from typing import Dict, List, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from src.database.dependency import get_db_session
from src.auth.dependencies import RoleChecker
from src.schemas.platform_services import SystemSettingResponse
from src.services.setting_service import SettingService

router = APIRouter(prefix="/settings", tags=["settings"])

# Admin-only check
admin_dependency = Depends(RoleChecker(["Admin", "CEO"]))


@router.get("/system", response_model=List[SystemSettingResponse], dependencies=[admin_dependency])
async def list_settings(
    category: Optional[str] = None,
    db: AsyncSession = Depends(get_db_session)
):
    """
    Lists system settings configurations. Restricted to administrators.
    """
    service = SettingService(db)
    settings = await service.list_settings(category=category)
    return settings


@router.put("/system", response_model=List[SystemSettingResponse], dependencies=[admin_dependency])
async def update_settings(
    settings_data: Dict[str, str],
    db: AsyncSession = Depends(get_db_session)
):
    """
    Updates one or multiple system configurations. Restricted to administrators.
    """
    service = SettingService(db)
    updated = []
    for key, val in settings_data.items():
        setting = await service.update_setting(key, val)
        updated.append(setting)
    return updated
