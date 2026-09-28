from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from src.database.dependency import get_db_session
from src.auth.dependencies import get_current_user, PermissionChecker
from src.models.auth import User
from src.schemas.purchase_requisition import PRCreate, PRUpdate, PRSchema, PRAllocateInventoryRequest
from src.services.pr_service import PRService

router = APIRouter(prefix="/pr", tags=["Purchase Requisitions"])


async def check_pr_access(pr, current_user: User, db: AsyncSession) -> None:
    """
    Validates user authorization access to a Purchase Requisition.
    - Admin: Full Access.
    - Manager: Department requisitions.
    - Procurement: Only approved PRs.
    - Employee/Others: Own requisitions only.
    """
    # If Draft, only requestor can access
    if pr.status == "Draft" and pr.requestor_id != current_user.user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only the owner can access their drafts."
        )

    if pr.requestor_id == current_user.user_id:
        return
        
    user_roles = [role.role_name for role in current_user.roles]
    
    if "Manager" in user_roles:
        if getattr(pr.requestor, "manager_id", None) == current_user.user_id:
            return

    if "Procurement" in user_roles:
        if pr.status in ("Approved", "Assigned to Procurement", "Procurement In Progress", "Completed"):
            return
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Procurement can only access fully approved requisitions."
        )

    from src.models.approval import ApprovalWorkflow, ApprovalStep, ApprovalHistory
    from sqlalchemy import select
    
    wf_query = select(ApprovalWorkflow.workflow_id).where(ApprovalWorkflow.pr_id == pr.pr_id)
    wf_res = await db.execute(wf_query)
    wf_id = wf_res.scalar_one_or_none()
    
    if wf_id:
        step_query = select(ApprovalStep).where(
            ApprovalStep.workflow_id == wf_id,
            (ApprovalStep.approver_id == current_user.user_id) | 
            (ApprovalStep.approver_id.is_(None) & ApprovalStep.approver_role_id.in_([r.role_id for r in current_user.roles]))
        )
        step_res = await db.execute(step_query)
        if step_res.scalars().first():
            return
            
        hist_query = select(ApprovalHistory).join(ApprovalStep, ApprovalHistory.step_id == ApprovalStep.step_id).where(
            ApprovalStep.workflow_id == wf_id,
            ApprovalHistory.performed_by == current_user.user_id
        )
        hist_res = await db.execute(hist_query)
        if hist_res.scalars().first():
            return
            
    raise HTTPException(
        status_code=status.HTTP_403_FORBIDDEN,
        detail="You are not authorized to view this requisition."
    )


@router.post("", response_model=PRSchema, status_code=status.HTTP_201_CREATED)
async def create_pr(
    data: PRCreate,
    db: AsyncSession = Depends(get_db_session),
    current_user: User = Depends(get_current_user)
):
    if data.department_name != current_user.department_name or data.employee_type != current_user.employee_type:
        raise HTTPException(
            status_code=400,
            detail="Invalid department or employee type. Please use the values assigned to your employee profile."
        )
    service = PRService(db)
    return await service.create_pr(data, current_user.user_id)


@router.get("", response_model=List[PRSchema])
async def list_prs(
    db: AsyncSession = Depends(get_db_session),
    current_user: User = Depends(get_current_user)
):
    service = PRService(db)
    prs = await service.pr_repo.list_accessible_prs(current_user)
        
    return [pr for pr in prs if not (pr.status == "Draft" and pr.requestor_id != current_user.user_id)]


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

    await check_pr_access(pr, current_user, db)
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

    await check_pr_access(pr, current_user, db)
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

    await check_pr_access(pr, current_user, db)
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

    await check_pr_access(pr, current_user, db)
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

    await check_pr_access(pr, current_user, db)
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

    await check_pr_access(pr, current_user, db)
    return await service.clone_pr(id, current_user.user_id)


@router.post("/{id}/allocate-inventory", response_model=PRSchema)
async def allocate_inventory(
    id: int,
    data: PRAllocateInventoryRequest,
    db: AsyncSession = Depends(get_db_session),
    current_user: User = Depends(get_current_user)
):
    service = PRService(db)
    pr = await service.pr_repo.get_by_id(id)
    if not pr:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="PR not found")
        
    await check_pr_access(pr, current_user, db)
    return await service.allocate_inventory(id, data.asset_id, current_user.user_id)


@router.post("/{id}/initiate-procurement", response_model=PRSchema)
async def initiate_procurement(
    id: int,
    db: AsyncSession = Depends(get_db_session),
    current_user: User = Depends(get_current_user)
):
    service = PRService(db)
    pr = await service.pr_repo.get_by_id(id)
    if not pr:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="PR not found")
        
    await check_pr_access(pr, current_user, db)
    return await service.initiate_procurement(id, current_user.user_id)
