from typing import List
from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession
from src.auth.dependencies import PermissionChecker, get_current_user
from src.database.dependency import get_db_session
from src.models.auth import User
from src.schemas.organization import DepartmentCreate, DepartmentSchema, DepartmentUpdate
from src.services.organization_service import DepartmentService

router = APIRouter(tags=["Departments"])


@router.get("", response_model=List[DepartmentSchema])
async def list_departments(
    skip: int = 0,
    limit: int = 100,
    db: AsyncSession = Depends(get_db_session),
    current_user: User = Depends(get_current_user)
):
    """
    Lists all departments.
    """
    service = DepartmentService(db)
    return await service.list_departments(skip=skip, limit=limit)


@router.get("/{dept_id}", response_model=DepartmentSchema)
async def get_department(
    dept_id: int,
    db: AsyncSession = Depends(get_db_session),
    current_user: User = Depends(get_current_user)
):
    """
    Retrieves department details by ID.
    """
    service = DepartmentService(db)
    return await service.get_department(dept_id)


@router.post("", response_model=DepartmentSchema, status_code=status.HTTP_201_CREATED)
async def create_department(
    data: DepartmentCreate,
    db: AsyncSession = Depends(get_db_session),
    current_user: User = Depends(PermissionChecker("admin.settings"))
):
    """
    Creates a new department.
    """
    service = DepartmentService(db)
    return await service.create_department(data)


@router.put("/{dept_id}", response_model=DepartmentSchema)
async def update_department(
    dept_id: int,
    data: DepartmentUpdate,
    db: AsyncSession = Depends(get_db_session),
    current_user: User = Depends(PermissionChecker("admin.settings"))
):
    """
    Updates an existing department.
    """
    service = DepartmentService(db)
    return await service.update_department(dept_id, data)


@router.delete("/{dept_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_department(
    dept_id: int,
    db: AsyncSession = Depends(get_db_session),
    current_user: User = Depends(PermissionChecker("admin.settings"))
):
    """
    Deletes a department.
    """
    service = DepartmentService(db)
    await service.delete_department(dept_id)
