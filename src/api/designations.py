from typing import List
from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession
from src.auth.dependencies import PermissionChecker, get_current_user
from src.database.dependency import get_db_session
from src.models.auth import User
from src.schemas.organization import DesignationCreate, DesignationSchema, DesignationUpdate
from src.services.organization_service import DesignationService

router = APIRouter(tags=["Designations"])


@router.get("", response_model=List[DesignationSchema])
async def list_designations(
    skip: int = 0,
    limit: int = 100,
    db: AsyncSession = Depends(get_db_session),
    current_user: User = Depends(get_current_user)
):
    """
    Lists all designations.
    """
    service = DesignationService(db)
    return await service.list_designations(skip=skip, limit=limit)


@router.get("/{desig_id}", response_model=DesignationSchema)
async def get_designation(
    desig_id: int,
    db: AsyncSession = Depends(get_db_session),
    current_user: User = Depends(get_current_user)
):
    """
    Retrieves designation details by ID.
    """
    service = DesignationService(db)
    return await service.get_designation(desig_id)


@router.post("", response_model=DesignationSchema, status_code=status.HTTP_201_CREATED)
async def create_designation(
    data: DesignationCreate,
    db: AsyncSession = Depends(get_db_session),
    current_user: User = Depends(PermissionChecker("admin.settings"))
):
    """
    Creates a new designation.
    """
    service = DesignationService(db)
    return await service.create_designation(data)


@router.put("/{desig_id}", response_model=DesignationSchema)
async def update_designation(
    desig_id: int,
    data: DesignationUpdate,
    db: AsyncSession = Depends(get_db_session),
    current_user: User = Depends(PermissionChecker("admin.settings"))
):
    """
    Updates an existing designation.
    """
    service = DesignationService(db)
    return await service.update_designation(desig_id, data)


@router.delete("/{desig_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_designation(
    desig_id: int,
    db: AsyncSession = Depends(get_db_session),
    current_user: User = Depends(PermissionChecker("admin.settings"))
):
    """
    Deletes a designation.
    """
    service = DesignationService(db)
    await service.delete_designation(desig_id)
