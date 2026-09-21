from typing import List
import logging
from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from src.database.dependency import get_db_session
from src.auth.dependencies import get_current_user
from src.models.auth import User, User as UserModel
from src.schemas.approval import InboxApprovalWorkflowSchema
from src.services.approval_service import ApprovalService

logger = logging.getLogger(__name__)

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
    pending_workflows = []
    
    try:
        pending_workflows = await service.get_pending_approvals_for_user(current_user)
    except Exception as e:
        logger.error(f"Error fetching core approval workflows: {e}", exc_info=True)
        pending_workflows = []
    
    user_roles = [r.role_name for r in current_user.roles]
    has_manager = "Manager" in user_roles
    has_admin = "Admin" in user_roles
    has_cfo = "CFO" in user_roles
    has_finance_mgr = "Finance Manager" in user_roles or "Finance" in user_roles
    has_it = "IT" in user_roles

    # Fetch pending Asset Incidents where user is explicitly the approver
    try:
        from src.models.assets import AssetIncident, Asset
        from sqlalchemy import or_
        
        from sqlalchemy.orm import selectinload
        stmt = (
            select(AssetIncident, Asset, UserModel)
            .options(selectinload(UserModel.roles))
            .join(Asset, AssetIncident.asset_id == Asset.asset_id)
            .join(UserModel, AssetIncident.reporter_id == UserModel.user_id)
            .where(AssetIncident.status != "Draft")
        )
        
        conditions = []
        if has_manager:
            conditions.append((AssetIncident.status == "Reported") & (UserModel.manager_id == current_user.user_id))
            
        if conditions:
            stmt = stmt.where(or_(*conditions))
            result = await db.execute(stmt)
            for incident, asset, reporter in result.all():
                workflow_step = "Manager Review" if incident.status == "Reported" else "Pending Fulfillment"
                asset_name_str = getattr(asset, "model", None) or "Asset"
                reporter_name = f"{reporter.first_name} {reporter.last_name}" if reporter else "Employee"
                cost_val = getattr(incident, "estimated_cost", None)
                pending_workflows.append({
                    "workflow_id": incident.incident_id,
                    "entity_type": "AssetIncident",
                    "entity_id": incident.incident_id,
                    "current_step_sequence": 1,
                    "workflow_step": workflow_step,
                    "status": incident.status,
                    "created_at": incident.created_at,
                    "updated_at": incident.updated_at,
                    "requestor_id": incident.reporter_id,
                    "requestor_name": reporter_name,
                    "requestor_designation": reporter.designation if reporter and hasattr(reporter, 'designation') and reporter.designation else (", ".join(r.role_name for r in reporter.roles) if reporter and hasattr(reporter, 'roles') and reporter.roles else "Employee"),
                    "title": f"{incident.incident_type} Issue: {asset_name_str} ({getattr(asset, 'asset_tag', 'ASSET')})",
                    "justification": incident.description,
                    "total_amount": cost_val,
                    "amount": cost_val,
                    "past_approvers": [],
                    "pending_approvers": ["Manager"],
                    "steps": [],
                    "can_approve": True
                })
    except Exception as e:
        logger.error(f"Error fetching pending Asset Incidents: {e}", exc_info=True)

    # Fetch Expense Reports where user is explicitly the approver
    try:
        from src.models.expense import ExpenseReport, ExpenseApproval
        
        from sqlalchemy.orm import selectinload
        from sqlalchemy import or_
        from src.models.auth import Role
        stmt = (
            select(ExpenseReport, UserModel)
            .options(selectinload(UserModel.roles))
            .join(UserModel, ExpenseReport.employee_id == UserModel.user_id)
            .outerjoin(ExpenseApproval, (ExpenseApproval.expense_report_id == ExpenseReport.expense_report_id) & (ExpenseApproval.status == "Pending"))
            .where(
                ExpenseReport.employee_id != current_user.user_id,
                ExpenseReport.status != "Draft"
            )
        )
        
        conditions = [ExpenseApproval.approver_id == current_user.user_id]
        
        # Finance Managers can see Payment Requested items, EXCEPT those from Admin/CEO/CFO
        if has_finance_mgr:
            conditions.append(
                (ExpenseReport.status == "Payment Requested") & 
                (~UserModel.roles.any(Role.role_name.in_(["Admin", "CEO", "CFO", "SuperAdmin"])))
            )
            
        # Admin and CFO can see all Payment Requested items
        if has_admin or has_cfo:
            conditions.append(ExpenseReport.status == "Payment Requested")
            
        stmt = stmt.where(or_(*conditions))
        
        result = await db.execute(stmt)
        
        seen_reports = set()
        for report, requestor in result.all():
            if report.expense_report_id in seen_reports:
                continue
            seen_reports.add(report.expense_report_id)
            
            workflow_step = report.status
            requestor_name = f"{requestor.first_name} {requestor.last_name}" if requestor else "Employee"
            pending_workflows.append({
                "workflow_id": report.expense_report_id,
                "entity_type": "ExpenseReport",
                "entity_id": report.expense_report_id,
                "current_step_sequence": 1,
                "workflow_step": workflow_step,
                "status": report.status,
                "created_at": report.created_at,
                "updated_at": report.updated_at,
                "requestor_id": report.employee_id,
                "requestor_name": requestor_name,
                "requestor_designation": requestor.designation if requestor and hasattr(requestor, 'designation') and requestor.designation else (", ".join(r.role_name for r in requestor.roles) if requestor and hasattr(requestor, 'roles') and requestor.roles else "Employee"),
                "title": f"{report.purpose} - {report.currency} {report.total_amount}",
                "justification": report.justification,
                "total_amount": report.total_amount,
                "amount": report.total_amount,
                "past_approvers": [],
                "pending_approvers": [workflow_step.replace("Pending ", "").replace(" Approval", "")],
                "steps": [],
                "can_approve": True
            })
    except Exception as e:
        logger.error(f"Error fetching pending Expense Reports: {e}", exc_info=True)

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
