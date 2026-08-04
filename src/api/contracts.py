from typing import List, Optional
from datetime import date
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from src.database.dependency import get_db_session
from src.auth.dependencies import get_current_user
from src.models.auth import User
from src.schemas.contract import ContractCreate, ContractUpdate, ContractSchema
from src.services.contract_service import ContractService

router = APIRouter(prefix="/contracts", tags=["Contracts"])


def enforce_contract_access(current_user: User) -> None:
    user_roles = [role.role_name for role in current_user.roles]
    allowed = ("Admin", "Procurement Officer", "Procurement Manager")
    if not any(role in allowed for role in user_roles):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You do not possess the authorization permissions required to manage contracts"
        )


@router.post("", response_model=ContractSchema, status_code=status.HTTP_201_CREATED)
async def create_contract(
    data: ContractCreate,
    db: AsyncSession = Depends(get_db_session),
    current_user: User = Depends(get_current_user)
):
    enforce_contract_access(current_user)
    service = ContractService(db)
    return await service.create_contract(data)


@router.get("", response_model=List[ContractSchema])
async def list_contracts(
    db: AsyncSession = Depends(get_db_session),
    current_user: User = Depends(get_current_user)
):
    enforce_contract_access(current_user)
    service = ContractService(db)
    return await service.contract_repo.list_all()


@router.get("/expiring", response_model=List[ContractSchema])
async def list_expiring_contracts(
    db: AsyncSession = Depends(get_db_session),
    current_user: User = Depends(get_current_user)
):
    enforce_contract_access(current_user)
    service = ContractService(db)
    return await service.check_expirations_and_reminders()


@router.get("/{id}", response_model=ContractSchema)
async def get_contract(
    id: int,
    db: AsyncSession = Depends(get_db_session),
    current_user: User = Depends(get_current_user)
):
    enforce_contract_access(current_user)
    service = ContractService(db)
    contract = await service.contract_repo.get_by_id(id)
    if not contract:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Contract not found")
    return contract


@router.put("/{id}", response_model=ContractSchema)
async def update_contract(
    id: int,
    data: ContractUpdate,
    db: AsyncSession = Depends(get_db_session),
    current_user: User = Depends(get_current_user)
):
    enforce_contract_access(current_user)
    service = ContractService(db)
    return await service.update_contract(id, data)


@router.post("/{id}/renew", response_model=ContractSchema)
async def renew_subscription(
    id: int,
    new_end_date: date,
    new_license_count: Optional[int] = None,
    db: AsyncSession = Depends(get_db_session),
    current_user: User = Depends(get_current_user)
):
    enforce_contract_access(current_user)
    service = ContractService(db)
    return await service.renew_subscription(id, new_end_date, new_license_count)
