from typing import List
from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession
from src.auth.dependencies import PermissionChecker, get_current_user
from src.database.dependency import get_db_session
from src.models.auth import User
from src.schemas.organization import BudgetCodeCreate, BudgetCodeSchema, BudgetCodeUpdate
from src.services.organization_service import BudgetCodeService

router = APIRouter(tags=["Budget Codes"])


@router.get("", response_model=List[BudgetCodeSchema])
async def list_budget_codes(
    skip: int = 0,
    limit: int = 100,
    db: AsyncSession = Depends(get_db_session),
    current_user: User = Depends(get_current_user)
):
    """
    Lists all budget codes.
    """
    service = BudgetCodeService(db)
    return await service.list_budget_codes(skip=skip, limit=limit)


@router.get("/{bc_id}", response_model=BudgetCodeSchema)
async def get_budget_code(
    bc_id: int,
    db: AsyncSession = Depends(get_db_session),
    current_user: User = Depends(get_current_user)
):
    """
    Retrieves budget code details by ID.
    """
    service = BudgetCodeService(db)
    return await service.get_budget_code(bc_id)


@router.post("", response_model=BudgetCodeSchema, status_code=status.HTTP_201_CREATED)
async def create_budget_code(
    data: BudgetCodeCreate,
    db: AsyncSession = Depends(get_db_session),
    current_user: User = Depends(PermissionChecker("admin.settings"))
):
    """
    Creates a new budget code.
    """
    service = BudgetCodeService(db)
    return await service.create_budget_code(data)


@router.put("/{bc_id}", response_model=BudgetCodeSchema)
async def update_budget_code(
    bc_id: int,
    data: BudgetCodeUpdate,
    db: AsyncSession = Depends(get_db_session),
    current_user: User = Depends(PermissionChecker("admin.settings"))
):
    """
    Updates an existing budget code.
    """
    service = BudgetCodeService(db)
    return await service.update_budget_code(bc_id, data)


@router.delete("/{bc_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_budget_code(
    bc_id: int,
    db: AsyncSession = Depends(get_db_session),
    current_user: User = Depends(PermissionChecker("admin.settings"))
):
    """
    Deletes a budget code.
    """
    service = BudgetCodeService(db)
    await service.delete_budget_code(bc_id)
