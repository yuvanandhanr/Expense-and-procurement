from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from src.database.dependency import get_db_session
from src.auth.dependencies import get_current_user
from src.models.auth import User, Role
from src.models.approval import ApprovalStep, ApprovalWorkflow
from src.models.purchase_requisition import PurchaseRequisition
from src.schemas.purchase_requisition import PRSchema
from sqlalchemy import select
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


def verify_approver_role_sync(step: ApprovalStep, current_user: User) -> None:
    # Deprecated sync version, unused but keeping signature for history. Use async version.
    pass

async def verify_approver_role(step: ApprovalStep, current_user: User, db: AsyncSession) -> None:
    """
    Enforces that the user has the required role (or Admin/CEO status) to approve/action the step.
    Prevents self-approval of own requests.
    """
    # Check requestor self-approval first
    workflow = await db.execute(select(ApprovalWorkflow).where(ApprovalWorkflow.workflow_id == step.workflow_id))
    workflow = workflow.scalar_one_or_none()
    if workflow:
        pr = await db.execute(select(PurchaseRequisition).where(PurchaseRequisition.pr_id == workflow.pr_id))
        pr = pr.scalar_one_or_none()
        if pr and pr.requestor_id == current_user.user_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You cannot approve your own request."
            )

    user_roles = [role.role_name for role in current_user.roles]
    if "Admin" in user_roles or "CEO" in user_roles:
        return

    # Check if specifically assigned to this user
    if step.approver_id is not None and step.approver_id == current_user.user_id:
        return

    # Resolve required role name for this step
    res = await db.execute(select(Role).where(Role.role_id == step.approver_role_id))
    step_role = res.scalar_one_or_none()
    required_role = step_role.role_name if step_role else ""

    # Manager Step (Step 1)
    if required_role == "Manager":
        if any(r in ["Manager", "Admin", "CEO", "Finance Manager", "CFO"] for r in user_roles):
            return

    # Finance Step (Step 2)
    if required_role in ["Finance", "Finance Manager"]:
        if any(r in ["Finance", "Finance Manager", "CFO", "Admin", "CEO"] for r in user_roles):
            return

    # CFO Step (Step 3)
    if required_role == "CFO":
        if any(r in ["CFO", "CEO", "Admin"] for r in user_roles):
            return

    user_role_ids = [role.role_id for role in current_user.roles]
    if step.approver_role_id in user_role_ids:
        return

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
    await verify_approver_role(active_step, current_user, db)
    return await service.approve_step(id, current_user.user_id, data.comments, getattr(data, "physical_inspection_done", False))


@router.post("/{id}/reject", response_model=PRSchema)
async def reject_pr(
    id: int,
    data: PRRejectRequest,
    db: AsyncSession = Depends(get_db_session),
    current_user: User = Depends(get_current_user)
):
    service = ApprovalService(db)
    active_step = await service.get_active_step(id)
    await verify_approver_role(active_step, current_user, db)
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
    await verify_approver_role(active_step, current_user, db)
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
    await verify_approver_role(active_step, current_user, db)
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
    await verify_approver_role(active_step, current_user, db)
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
