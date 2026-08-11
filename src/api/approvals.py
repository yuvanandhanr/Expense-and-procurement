from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from src.database.dependency import get_db_session
from src.auth.dependencies import get_current_user
from src.models.auth import User
from src.models.approval import ApprovalStep
from src.schemas.purchase_requisition import PRSchema
from src.schemas.approval import (
    PRApproveRequest,
    PRRejectRequest,
    PRReturnRequest,
    PRDelegateRequest,
    PREscalateRequest,
    WorkflowHistorySchema,
    ApprovalWorkflowSchema,
)
from src.services.approval_service import ApprovalService

router = APIRouter(prefix="/pr", tags=["Approvals"])


def verify_approver_role(step: ApprovalStep, current_user: User) -> None:
    """
    Enforces that the user has the required role (or Admin status) to approve/action the step.
    If a specific approver_id is assigned, strictly enforce it.
    """
    user_roles = [role.role_name for role in current_user.roles]
    if "Admin" in user_roles:
        return

    if step.approver_id is not None:
        if current_user.user_id != step.approver_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You are not the designated approver for this step."
            )
        return

    user_role_ids = [role.role_id for role in current_user.roles]
    if step.approver_role_id not in user_role_ids:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You do not possess the required role to action this approval step"
        )


@router.post("/{id}/approve", response_model=PRSchema)
async def approve_pr(
    id: int,
    data: PRApproveRequest,
    db: AsyncSession = Depends(get_db_session),
    current_user: User = Depends(get_current_user)
):
    service = ApprovalService(db)
    active_step = await service.get_active_step(id)
    verify_approver_role(active_step, current_user)
    return await service.approve_step(id, current_user.user_id, data.comments)


@router.post("/{id}/reject", response_model=PRSchema)
async def reject_pr(
    id: int,
    data: PRRejectRequest,
    db: AsyncSession = Depends(get_db_session),
    current_user: User = Depends(get_current_user)
):
    service = ApprovalService(db)
    active_step = await service.get_active_step(id)
    verify_approver_role(active_step, current_user)
    return await service.reject_step(id, current_user.user_id, data.comments)


@router.post("/{id}/return", response_model=PRSchema)
async def return_pr(
    id: int,
    data: PRReturnRequest,
    db: AsyncSession = Depends(get_db_session),
    current_user: User = Depends(get_current_user)
):
    service = ApprovalService(db)
    active_step = await service.get_active_step(id)
    verify_approver_role(active_step, current_user)
    return await service.return_step(id, current_user.user_id, data.comments)


@router.post("/{id}/delegate", response_model=PRSchema)
async def delegate_pr(
    id: int,
    data: PRDelegateRequest,
    db: AsyncSession = Depends(get_db_session),
    current_user: User = Depends(get_current_user)
):
    service = ApprovalService(db)
    active_step = await service.get_active_step(id)
    verify_approver_role(active_step, current_user)
    return await service.delegate_step(id, current_user.user_id, data.delegate_to_user_id, data.comments)


@router.post("/{id}/escalate", response_model=PRSchema)
async def escalate_pr(
    id: int,
    data: PREscalateRequest,
    db: AsyncSession = Depends(get_db_session),
    current_user: User = Depends(get_current_user)
):
    service = ApprovalService(db)
    active_step = await service.get_active_step(id)
    verify_approver_role(active_step, current_user)
    return await service.escalate_step(id, current_user.user_id, data.comments)


@router.get("/{id}/history", response_model=List[WorkflowHistorySchema])
async def get_pr_history(
    id: int,
    db: AsyncSession = Depends(get_db_session),
    current_user: User = Depends(get_current_user)
):
    service = ApprovalService(db)
    # Check access to PR
    from src.api.purchase_requisitions import check_pr_access
    pr = await service.pr_repo.get_by_id(id)
    if not pr:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="PR not found")
    check_pr_access(pr, current_user)
    
    return await service.workflow_history_repo.list_by_pr_id(id)


@router.get("/{id}/approvals", response_model=ApprovalWorkflowSchema)
async def get_pr_approvals(
    id: int,
    db: AsyncSession = Depends(get_db_session),
    current_user: User = Depends(get_current_user)
):
    service = ApprovalService(db)
    # Check access to PR
    from src.api.purchase_requisitions import check_pr_access
    pr = await service.pr_repo.get_by_id(id)
    if not pr:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="PR not found")
    check_pr_access(pr, current_user)

    workflow = await service.workflow_repo.get_by_pr_id(id)
    if not workflow:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="No workflow started for this PR")
    return workflow
