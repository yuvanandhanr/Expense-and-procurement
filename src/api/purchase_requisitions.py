from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from src.database.dependency import get_db_session
from src.auth.dependencies import get_current_user, PermissionChecker
from src.models.auth import User
from src.schemas.purchase_requisition import PRCreate, PRUpdate, PRSchema
from src.services.pr_service import PRService

router = APIRouter(prefix="/pr", tags=["Purchase Requisitions"])


def check_pr_access(pr, current_user: User) -> None:
    """
    Validates user authorization access to a Purchase Requisition.
    - Admin: Full Access.
    - Manager: Department requisitions.
    - Procurement: Only approved PRs.
    - Employee/Others: Own requisitions only.
    """
    # Check full access roles
    user_roles = [role.role_name for role in current_user.roles]
    if any(role in user_roles for role in ["Admin", "CFO", "Finance Manager", "Finance", "Manager", "CEO"]):
        return

    # Check Procurement role
    if "Procurement" in user_roles:
        if pr.status in ("Approved", "Assigned to Procurement", "Procurement In Progress", "Completed"):
            return
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Procurement can only access fully approved requisitions."
        )

    # Check Manager role
    if "Manager" in user_roles and current_user.department_id:
        if pr.department_id == current_user.department_id:
            return

    # Fallback to Requestor check
    if pr.requestor_id != current_user.user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You are restricted to accessing your own requisitions only"
        )


@router.post("", response_model=PRSchema, status_code=status.HTTP_201_CREATED)
async def create_pr(
    data: PRCreate,
    db: AsyncSession = Depends(get_db_session),
    current_user: User = Depends(get_current_user)
):
    service = PRService(db)
    return await service.create_pr(data, current_user.user_id)


@router.get("", response_model=List[PRSchema])
async def list_prs(
    db: AsyncSession = Depends(get_db_session),
    current_user: User = Depends(get_current_user)
):
    service = PRService(db)
    user_roles = [role.role_name for role in current_user.roles]

    if any(role in user_roles for role in ["Admin", "CFO", "Finance Manager", "Finance", "Procurement", "CEO"]):
        return await service.pr_repo.list_all()
    elif "Manager" in user_roles and current_user.department_id:
        return await service.pr_repo.list_by_department(current_user.department_id)
    else:
        return await service.pr_repo.list_by_requestor(current_user.user_id)


@router.get("/{id}", response_model=PRSchema)
async def get_pr(
    id: int,
    db: AsyncSession = Depends(get_db_session),
    current_user: User = Depends(get_current_user)
):
    service = PRService(db)
    pr = await service.pr_repo.get_by_id(id)
    if not pr:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Purchase Requisition not found")

    check_pr_access(pr, current_user)
    return pr


@router.put("/{id}", response_model=PRSchema)
async def update_pr(
    id: int,
    data: PRUpdate,
    db: AsyncSession = Depends(get_db_session),
    current_user: User = Depends(get_current_user)
):
    service = PRService(db)
    pr = await service.pr_repo.get_by_id(id)
    if not pr:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Purchase Requisition not found")

    check_pr_access(pr, current_user)
    return await service.update_pr(id, data, current_user.user_id)


@router.delete("/{id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_pr(
    id: int,
    db: AsyncSession = Depends(get_db_session),
    current_user: User = Depends(get_current_user)
):
    service = PRService(db)
    pr = await service.pr_repo.get_by_id(id)
    if not pr:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Purchase Requisition not found")

    check_pr_access(pr, current_user)
    if pr.status not in ("Draft", "Returned for Modification"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Only draft or returned requisitions can be deleted"
        )
    await service.pr_repo.delete(id)


@router.post("/{id}/submit", response_model=PRSchema)
async def submit_pr(
    id: int,
    db: AsyncSession = Depends(get_db_session),
    current_user: User = Depends(get_current_user)
):
    service = PRService(db)
    pr = await service.pr_repo.get_by_id(id)
    if not pr:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="PR not found")

    check_pr_access(pr, current_user)
    return await service.submit_pr(id, current_user.user_id)


@router.post("/{id}/cancel", response_model=PRSchema)
async def cancel_pr(
    id: int,
    db: AsyncSession = Depends(get_db_session),
    current_user: User = Depends(get_current_user)
):
    service = PRService(db)
    pr = await service.pr_repo.get_by_id(id)
    if not pr:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="PR not found")

    check_pr_access(pr, current_user)
    return await service.cancel_pr(id, current_user.user_id)


@router.post("/{id}/clone", response_model=PRSchema, status_code=status.HTTP_201_CREATED)
async def clone_pr(
    id: int,
    db: AsyncSession = Depends(get_db_session),
    current_user: User = Depends(get_current_user)
):
    service = PRService(db)
    pr = await service.pr_repo.get_by_id(id)
    if not pr:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="PR not found")

    check_pr_access(pr, current_user)
    return await service.clone_pr(id, current_user.user_id)
