from typing import List
from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession
from src.auth.dependencies import PermissionChecker
from src.database.dependency import get_db_session
from src.schemas.auth import PermissionCreate, PermissionSchema, ErrorResponse
from src.services.auth_service import PermissionService

router = APIRouter(prefix="/permissions", tags=["permissions"])


@router.get(
    "",
    response_model=List[PermissionSchema],
    dependencies=[Depends(PermissionChecker("users.view"))],
    responses={
        401: {"model": ErrorResponse, "description": "Not authenticated"},
        403: {"model": ErrorResponse, "description": "Permission denied"}
    }
)
async def list_permissions(
    skip: int = 0,
    limit: int = 100,
    db: AsyncSession = Depends(get_db_session)
):
    """
    Lists all permissions registered in the system. Requires users.view permission.
    """
    permission_service = PermissionService(db)
    return await permission_service.list_permissions(skip=skip, limit=limit)


@router.post(
    "",
    response_model=PermissionSchema,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(PermissionChecker("admin.settings"))],
    responses={
        401: {"model": ErrorResponse, "description": "Not authenticated"},
        403: {"model": ErrorResponse, "description": "Permission denied"}
    }
)
async def create_permission(
    data: PermissionCreate,
    db: AsyncSession = Depends(get_db_session)
):
    """
    Registers a new system permission code.
    """
    permission_service = PermissionService(db)
    return await permission_service.create_permission(data)
