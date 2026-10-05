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
    # Fetch all accessible Expenses for the current user (excluding their own, which are in My Reimbursements)
    from sqlalchemy import select
    from sqlalchemy.orm import selectinload
    from src.models.expense import ExpenseReport, ExpenseApproval
    from src.models.auth import User as UserModel
    from src.api.expenses import _can_access_report
    
    stmt_exp_all = (
        select(ExpenseReport)
        .options(
            selectinload(ExpenseReport.approvals),
            selectinload(ExpenseReport.employee).selectinload(UserModel.roles)
        )
        .where(ExpenseReport.employee_id != current_user.user_id)
        .order_by(ExpenseReport.created_at.desc())
    )
    result_exp_all = await db.execute(stmt_exp_all)
    user_roles_set = {r.role_name for r in current_user.roles}
    
    for report in result_exp_all.scalars().unique().all():
        if _can_access_report(report, current_user):
            can_approve = False
            pending_app = next((a for a in report.approvals if a.status == "Pending"), None)
            if pending_app and pending_app.approver_id == current_user.user_id:
                can_approve = True
            elif report.status in ["Payment Requested", "Approved for Payment"] and bool(user_roles_set & {"Finance Manager", "CFO"}):
                can_approve = True
                
            pending_workflows.append({
                "workflow_id": pending_app.approval_id if pending_app else report.expense_report_id,
                "entity_type": "ExpenseReport",
                "entity_id": report.expense_report_id,
                "current_step_sequence": 1,
                "workflow_step": report.status,
                "status": report.status,
                "created_at": report.created_at,
                "updated_at": report.updated_at,
                "requestor_id": report.employee_id,
                "requestor_name": f"{report.employee.first_name} {report.employee.last_name}",
                "title": f"Expense: {report.purpose}",
                "justification": report.justification,
                "amount": float(report.total_amount) if report.total_amount else 0.0,
                "past_approvers": [],
                "pending_approvers": [f"User {pending_app.approver_id}"] if pending_app else [],
                "steps": [],
                "can_approve": can_approve
            })
    
    # Also fetch pending Asset Incidents for Admin/Manager
    user_roles = [r.role_name for r in current_user.roles]
    if any(r in user_roles for r in ["Admin", "Manager", "IT"]):
        from sqlalchemy import select
        from src.models.assets import AssetIncident, Asset
        from src.models.auth import User as UserModel
        
        # Determine status filter based on role
        statuses = []
        if "Manager" in user_roles:
            statuses.extend(["Submitted", "Manager Approved", "Rejected", "Returned for Correction"])
        if "Admin" in user_roles or "IT" in user_roles:
            statuses.extend(["Submitted", "Manager Approved", "Admin Approved", "Waiting for Procurement", "Approved", "Resolved", "Resolved / Completed", "Rejected", "Returned for Correction"])
        statuses = list(set(statuses))
            
        stmt = (
            select(AssetIncident, Asset, UserModel)
            .join(Asset, AssetIncident.asset_id == Asset.asset_id)
            .join(UserModel, AssetIncident.reporter_id == UserModel.user_id)
            .where(AssetIncident.status.in_(statuses))
            .order_by(AssetIncident.created_at.desc())
        )
        
        # If just a Manager, only see incidents in their department and not their own
        if "Manager" in user_roles and "Admin" not in user_roles and "IT" not in user_roles:
            stmt = stmt.where(Asset.department_id == current_user.department_id)
            
        result = await db.execute(stmt)
        for incident, asset, reporter in result.all():
            can_approve = False
            # Self-approval prevented
            if incident.reporter_id != current_user.user_id:
                if incident.status == "Submitted" and ("Manager" in user_roles or "Admin" in user_roles):
                    can_approve = True
                elif incident.status == "Manager Approved" and ("Admin" in user_roles or "IT" in user_roles):
                    can_approve = True
                elif incident.status in ["Admin Approved", "Waiting for Procurement"] and ("Admin" in user_roles or "IT" in user_roles):
                    can_approve = True

            workflow_step = "Manager Review" if incident.status == "Submitted" else ("Admin Review" if incident.status == "Manager Approved" else "Fulfillment")
            asset_name_str = asset.model if asset.model else "Asset"
            pending_workflows.append({
                "workflow_id": incident.incident_id,
                "entity_type": "AssetIncident",
                "entity_id": incident.incident_id,
                "current_step_sequence": 1 if incident.status == "Submitted" else 2,
                "workflow_step": workflow_step,
                "status": incident.status,
                "created_at": incident.created_at,
                "updated_at": incident.updated_at,
                "requestor_id": incident.reporter_id,
                "requestor_name": f"{reporter.first_name} {reporter.last_name}",
                "title": f"{incident.incident_type} Issue: {asset_name_str} ({asset.asset_tag})",
                "justification": incident.description,
                "past_approvers": [],
                "pending_approvers": ["Admin/Manager"],
                "steps": [],
                "can_approve": can_approve,
                "reason": incident.reason,
                "incident_type": incident.incident_type,
                "asset_tag": asset.asset_tag,
                "asset_name": asset.model,
                "serial_number": asset.serial_number,
                "attachment_url": incident.attachment_url,
                "incident_date": str(incident.incident_date) if incident.incident_date else None,
                "manager_inspection_assessment": incident.manager_inspection_assessment,
                "manager_inspection_comments": incident.manager_inspection_comments,
                "admin_inspection_resolution": incident.admin_inspection_resolution,
                "admin_comments": incident.admin_comments,
                "linked_pr_id": incident.linked_pr_id
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
