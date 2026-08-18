from typing import List
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from src.database.dependency import get_db_session
from src.auth.dependencies import get_current_user
from src.models.auth import User
from src.schemas.approval import InboxApprovalWorkflowSchema
from src.services.approval_service import ApprovalService

router = APIRouter(prefix="/approvals", tags=["Approvals Inbox"])

@router.get("", response_model=List[InboxApprovalWorkflowSchema])
async def get_pending_approvals(
    db: AsyncSession = Depends(get_db_session),
    current_user: User = Depends(get_current_user)
):
    """
    Fetch all pending approval workflows for the current user based on their roles and explicit step assignments.
    """
    service = ApprovalService(db)
    pending_workflows = await service.get_pending_approvals_for_user(current_user)
    return pending_workflows

@router.delete("/{workflow_id}")
async def cancel_approval_workflow(
    workflow_id: int,
    db: AsyncSession = Depends(get_db_session),
    current_user: User = Depends(get_current_user)
):
    """
    Cancel an approval workflow by the requestor.
    """
    service = ApprovalService(db)
    success = await service.cancel_workflow(workflow_id, current_user.user_id)
    return {"message": "Approval workflow cancelled successfully"}
