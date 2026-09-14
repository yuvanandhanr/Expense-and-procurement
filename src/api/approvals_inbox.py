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
    
    # Also fetch pending Asset Incidents for Admin/Manager
    user_roles = [r.role_name for r in current_user.roles]
    if any(r in user_roles for r in ["Admin", "Manager", "IT"]):
        from sqlalchemy import select
        from src.models.assets import AssetIncident, Asset
        from src.models.auth import User as UserModel
        
        # Determine status filter based on role
        statuses = []
        if "Manager" in user_roles:
            statuses.append("Reported")
        if "Admin" in user_roles or "IT" in user_roles:
            statuses.append("Pending Fulfillment")
            statuses.append("Waiting for Procurement")
            
        stmt = (
            select(AssetIncident, Asset, UserModel)
            .join(Asset, AssetIncident.asset_id == Asset.asset_id)
            .join(UserModel, AssetIncident.reporter_id == UserModel.user_id)
            .where(AssetIncident.status.in_(statuses))
        )
        
        # If just a Manager, only see incidents in their department
        if "Manager" in user_roles and "Admin" not in user_roles and "IT" not in user_roles:
            stmt = stmt.where(Asset.department_id == current_user.department_id)
            
        result = await db.execute(stmt)
        for incident, asset, reporter in result.all():
            # Exclude Approved incidents if the user is a Manager who is not an Admin/IT
            # (Handled by the status filter above)
            workflow_step = "Manager Review" if incident.status == "Reported" else "Pending Fulfillment"
            asset_name_str = asset.model if asset.model else "Asset"
            pending_workflows.append({
                "workflow_id": incident.incident_id, # using incident_id as workflow_id since entity_type distinguishes it
                "entity_type": "AssetIncident",
                "entity_id": incident.incident_id,
                "current_step_sequence": 1,
                "workflow_step": workflow_step,
                "status": incident.status,
                "created_at": incident.created_at,
                "updated_at": incident.updated_at,
                "requestor_id": incident.reporter_id,
                "requestor_name": f"{reporter.first_name} {reporter.last_name}",
                "title": f"{incident.incident_type} Issue: {asset_name_str} ({asset.asset_tag})",
                "justification": incident.description,
                "total_amount": incident.estimated_cost,
                "amount": incident.estimated_cost,
                "past_approvers": [],
                "pending_approvers": ["Admin/Manager"],
                "steps": [],
                "can_approve": True
            })

    # Fetch pending Expense Reports for the current user
    from src.models.expense import ExpenseReport
    
    # Determine which statuses this user can approve
    expense_statuses = []
    has_manager = "Manager" in user_roles
    has_admin = "Admin" in user_roles
    has_cfo = "CFO" in user_roles
    has_finance_mgr = "Finance Manager" in user_roles or "Finance" in user_roles

    if has_manager or has_admin:
        expense_statuses.append("Pending Manager Approval")
    if has_finance_mgr or has_cfo or has_admin:
        expense_statuses.extend(["Pending Finance Approval", "Pending Finance Manager Approval", "Payment Requested"])
    if has_cfo or has_admin:
        expense_statuses.append("Pending CFO Approval")

    if expense_statuses:
        # Build query
        stmt = (
            select(ExpenseReport, UserModel)
            .join(UserModel, ExpenseReport.employee_id == UserModel.user_id)
            .where(
                ExpenseReport.status.in_(expense_statuses),
                ExpenseReport.employee_id != current_user.user_id # DO NOT self-approve
            )
        )
        
        result = await db.execute(stmt)
        for report, requestor in result.all():
            # If the user is just a Manager, they should only approve for their team members
            if has_manager and not (has_admin or has_cfo or has_finance_mgr) and report.status == "Pending Manager Approval":
                if requestor.manager_id != current_user.user_id:
                    continue # Skip if not their direct manager

            workflow_step = report.status
            pending_workflows.append({
                "workflow_id": report.expense_report_id,
                "entity_type": "ExpenseReport",
                "entity_id": report.expense_report_id,
                "current_step_sequence": 1,
                "workflow_step": workflow_step,
                "status": report.status,
                "created_at": report.created_at or report.submission_date,
                "updated_at": report.updated_at,
                "requestor_id": report.employee_id,
                "requestor_name": f"{requestor.first_name} {requestor.last_name}",
                "title": f"{report.purpose} - {report.currency} {report.total_amount}",
                "justification": report.justification,
                "total_amount": report.total_amount,
                "amount": report.total_amount,
                "past_approvers": [],
                "pending_approvers": [workflow_step.replace("Pending ", "").replace(" Approval", "")],
                "steps": [],
                "can_approve": True
            })

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
