from typing import List
from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession
from src.auth.dependencies import PermissionChecker
from src.database.dependency import get_db_session
from src.schemas.auth import RoleCreate, RoleSchema, RoleUpdate, ErrorResponse
from src.services.auth_service import RoleService

router = APIRouter(prefix="/roles", tags=["roles"])


@router.get(
    "",
    response_model=List[RoleSchema],
    dependencies=[Depends(PermissionChecker("users.view"))],
    responses={
        401: {"model": ErrorResponse, "description": "Not authenticated"},
        403: {"model": ErrorResponse, "description": "Permission denied"}
    }
)
async def list_roles(
    skip: int = 0,
    limit: int = 100,
    db: AsyncSession = Depends(get_db_session)
):
    """
    Lists all roles registered in the system. Requires users.view permission.
    """
    role_service = RoleService(db)
    return await role_service.list_roles(skip=skip, limit=limit)


@router.get(
    "/{role_id}",
    response_model=RoleSchema,
    dependencies=[Depends(PermissionChecker("users.view"))],
    responses={
        401: {"model": ErrorResponse, "description": "Not authenticated"},
        403: {"model": ErrorResponse, "description": "Permission denied"},
        404: {"model": ErrorResponse, "description": "Role not found"}
    }
)
async def get_role(
    role_id: int,
    db: AsyncSession = Depends(get_db_session)
):
    """
    Retrieves details of a single role.
    """
    role_service = RoleService(db)
    return await role_service.get_role(role_id)


@router.post(
    "",
    response_model=RoleSchema,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(PermissionChecker("admin.settings"))],
    responses={
        401: {"model": ErrorResponse, "description": "Not authenticated"},
        403: {"model": ErrorResponse, "description": "Permission denied"}
    }
)
async def create_role(
    data: RoleCreate,
    db: AsyncSession = Depends(get_db_session)
):
    """
    Creates a new security role.
    """
    role_service = RoleService(db)
    return await role_service.create_role(data)


@router.put(
    "/{role_id}",
    response_model=RoleSchema,
    dependencies=[Depends(PermissionChecker("admin.settings"))],
    responses={
        401: {"model": ErrorResponse, "description": "Not authenticated"},
        403: {"model": ErrorResponse, "description": "Permission denied"},
        404: {"model": ErrorResponse, "description": "Role not found"}
    }
)
async def update_role(
    role_id: int,
    data: RoleUpdate,
    db: AsyncSession = Depends(get_db_session)
):
    """
    Updates an existing security role and its mapped permission associations.
    """
    role_service = RoleService(db)
    return await role_service.update_role(role_id, data)


@router.delete(
    "/{role_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    dependencies=[Depends(PermissionChecker("admin.settings"))],
    responses={
        401: {"model": ErrorResponse, "description": "Not authenticated"},
        403: {"model": ErrorResponse, "description": "Permission denied"},
        404: {"model": ErrorResponse, "description": "Role not found"}
    }
)
async def delete_role(
    role_id: int,
    db: AsyncSession = Depends(get_db_session)
):
    """
    Deletes a security role.
    """
    role_service = RoleService(db)
    await role_service.delete_role(role_id)
