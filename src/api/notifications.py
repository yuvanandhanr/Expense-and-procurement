from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from src.database.dependency import get_db_session
from src.auth.dependencies import get_current_user
from src.models.auth import User
from src.schemas.platform_services import NotificationResponse, NotificationPreferenceUpdate, NotificationPreferenceResponse
from src.services.notification_service import NotificationService

router = APIRouter(prefix="/notifications", tags=["notifications"])


@router.get("", response_model=List[NotificationResponse])
async def list_notifications(
    skip: int = 0,
    limit: int = 100,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session)
):
    """
    Retrieves the paginated list of notifications for the authenticated user.
    """
    service = NotificationService(db)
    notifications = await service.notification_repo.list_by_user(current_user.user_id, skip=skip, limit=limit)
    return notifications


@router.post("/{notification_id}/read")
async def mark_notification_read(
    notification_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session)
):
    """
    Marks a specific notification as Read.
    """
    service = NotificationService(db)
    success = await service.mark_as_read(notification_id, current_user.user_id)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Notification not found or access denied"
        )
    return {"status": "success", "message": "Notification marked as read"}


@router.post("/read-all")
async def mark_all_notifications_read(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session)
):
    """
    Marks all notifications for the authenticated user as Read.
    """
    service = NotificationService(db)
    count = await service.mark_all_as_read(current_user.user_id)
    return {"status": "success", "message": f"Marked {count} notifications as read"}


@router.get("/preferences", response_model=NotificationPreferenceResponse)
async def get_preferences(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session)
):
    """
    Retrieves the notification settings/preferences for the authenticated user.
    """
    service = NotificationService(db)
    pref = await service.get_or_create_preferences(current_user.user_id)
    return pref


@router.put("/preferences", response_model=NotificationPreferenceResponse)
async def update_preferences(
    data: NotificationPreferenceUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session)
):
    """
    Updates the notification settings/preferences for the authenticated user.
    """
    service = NotificationService(db)
    pref = await service.get_or_create_preferences(current_user.user_id)
    
    if data.email_enabled is not None:
        pref.email_enabled = data.email_enabled
    if data.in_app_enabled is not None:
        pref.in_app_enabled = data.in_app_enabled
    if data.categories is not None:
        pref.categories = data.categories
        
    await service.pref_repo.update(pref)
    return pref
