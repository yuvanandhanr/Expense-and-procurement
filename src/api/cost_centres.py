from typing import List
from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession
from src.auth.dependencies import PermissionChecker, get_current_user
from src.database.dependency import get_db_session
from src.models.auth import User
from src.schemas.organization import CostCenterCreate, CostCenterSchema, CostCenterUpdate
from src.services.organization_service import CostCenterService

router = APIRouter(tags=["Cost Centres"])


@router.get("", response_model=List[CostCenterSchema])
async def list_cost_centers(
    skip: int = 0,
    limit: int = 100,
    db: AsyncSession = Depends(get_db_session),
    current_user: User = Depends(get_current_user)
):
    """
    Lists all cost centers.
    """
    service = CostCenterService(db)
    return await service.list_cost_centers(skip=skip, limit=limit)


@router.get("/{cc_id}", response_model=CostCenterSchema)
async def get_cost_center(
    cc_id: int,
    db: AsyncSession = Depends(get_db_session),
    current_user: User = Depends(get_current_user)
):
    """
    Retrieves cost center details by ID.
    """
    service = CostCenterService(db)
    return await service.get_cost_center(cc_id)


@router.post("", response_model=CostCenterSchema, status_code=status.HTTP_201_CREATED)
async def create_cost_center(
    data: CostCenterCreate,
    db: AsyncSession = Depends(get_db_session),
    current_user: User = Depends(PermissionChecker("admin.settings"))
):
    """
    Creates a new cost center.
    """
    service = CostCenterService(db)
    return await service.create_cost_center(data)


@router.put("/{cc_id}", response_model=CostCenterSchema)
async def update_cost_center(
    cc_id: int,
    data: CostCenterUpdate,
    db: AsyncSession = Depends(get_db_session),
    current_user: User = Depends(PermissionChecker("admin.settings"))
):
    """
    Updates an existing cost center.
    """
    service = CostCenterService(db)
    return await service.update_cost_center(cc_id, data)


@router.delete("/{cc_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_cost_center(
    cc_id: int,
    db: AsyncSession = Depends(get_db_session),
    current_user: User = Depends(PermissionChecker("admin.settings"))
):
    """
    Deletes a cost center.
    """
    service = CostCenterService(db)
    await service.delete_cost_center(cc_id)
