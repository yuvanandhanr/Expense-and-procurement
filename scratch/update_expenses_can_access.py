import re

with open("src/api/expenses.py", "r") as f:
    content = f.read()

old_can = """def _can_access_report(report: ExpenseReport, user: User) -> bool:
    if report.status == "Draft":
        return report.employee_id == user.user_id

    if report.employee_id == user.user_id:
        return True

    # If user is the manager of the creator
    if getattr(report.employee, "manager_id", None) == user.user_id:
        return True

    # If user is in the approval chain for this report
    if any(app.approver_id == user.user_id for app in report.approvals):
        return True

    return False"""

new_can = """def _can_access_report(report: ExpenseReport, user: User) -> bool:
    if report.status == "Draft":
        return report.employee_id == user.user_id

    if report.employee_id == user.user_id:
        return True

    # If user is in the approval chain for this report
    if any(app.approver_id == user.user_id for app in report.approvals):
        return True

    # If user is the manager of the creator
    if getattr(report.employee, "manager_id", None) == user.user_id:
        user_roles = [r.role_name for r in user.roles] if hasattr(user, 'roles') else []
        is_admin = any(r in user_roles for r in ["Admin", "SuperAdmin", "CEO", "CFO"])
        
        creator_roles = [r.role_name for r in report.employee.roles] if hasattr(report.employee, 'roles') else []
        
        if not is_admin:
            if any(r in creator_roles for r in ["Admin", "CFO", "CEO", "Finance Manager"]):
                return False
        return True

    return False"""

content = content.replace(old_can, new_can)

with open("src/api/expenses.py", "w") as f:
    f.write(content)

