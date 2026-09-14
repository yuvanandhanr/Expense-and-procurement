import re

with open("src/api/approvals_inbox.py", "r") as f:
    content = f.read()

expense_logic = """
    # Fetch pending Expense Reports for the current user
    from sqlalchemy import select
    from src.models.expense import ExpenseReport
    from src.models.auth import User as UserModel
    
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
                "past_approvers": [],
                "pending_approvers": [workflow_step.replace("Pending ", "").replace(" Approval", "")],
                "steps": [],
                "can_approve": True
            })
"""

# Insert right before return pending_workflows
content = content.replace("    return pending_workflows", expense_logic + "\n    return pending_workflows")

with open("src/api/approvals_inbox.py", "w") as f:
    f.write(content)

