import re

with open("src/api/expenses.py", "r") as f:
    content = f.read()

old_can_access = r"def _can_access_report\(report: ExpenseReport, user: User\) -> bool:.*?(?=\ndef _can_act_on_pending_report)"
new_can_access = """def _can_access_report(report: ExpenseReport, user: User) -> bool:
    if report.status == "Draft":
        return report.employee_id == user.user_id

    if report.employee_id == user.user_id:
        return True

    # If user is in the approval chain for this report
    if any(app.approver_id == user.user_id for app in report.approvals):
        return True

    user_roles = [r.role_name for r in getattr(user, 'roles', [])]
    is_admin_or_exec = any(r in user_roles for r in ["Admin", "SuperAdmin", "CEO", "CFO"])
    
    # Admin, CFO, CEO can see all non-draft claims globally
    if is_admin_or_exec:
        return True
        
    has_finance_mgr = "Finance Manager" in user_roles or "Finance" in user_roles
    creator_roles = [r.role_name for r in getattr(report.employee, 'roles', [])]
    
    # Finance Managers can see claims pending manager approval or their stages, except from Admin/Execs
    if has_finance_mgr:
        if not any(r in creator_roles for r in ["Admin", "CEO", "CFO", "SuperAdmin"]):
            if report.status in ["Pending Manager Approval", "Pending Finance Manager Approval", "Payment Requested", "Approved for Payment", "Finance Rejected", "Closed"]:
                return True

    # If user is the manager of the creator
    if getattr(report.employee, "manager_id", None) == user.user_id:
        if not is_admin_or_exec:
            if any(r in creator_roles for r in ["Admin", "CFO", "CEO", "Finance Manager"]):
                return False
        return True

    return False"""

content = re.sub(old_can_access, new_can_access, content, flags=re.DOTALL)

with open("src/api/expenses.py", "w") as f:
    f.write(content)
