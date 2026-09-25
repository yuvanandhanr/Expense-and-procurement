import re

with open("src/api/expenses.py", "r") as f:
    content = f.read()

old_cond = """    user_roles = [r.role_name for r in current_user.roles]
    is_admin = any(r in user_roles for r in ["Admin", "SuperAdmin", "CEO", "CFO"])
    is_fin_mgr = "Finance Manager" in user_roles or "Finance" in user_roles
    is_manager = "Manager" in user_roles

    conditions = [
        ExpenseReport.employee_id == current_user.user_id,
        (ExpenseApproval.approver_id == current_user.user_id) & (ExpenseReport.status != 'Draft')
    ]

    if is_manager:
        manager_cond = (UserModel.manager_id == current_user.user_id) & (ExpenseReport.status != 'Draft')
        if not is_admin:
            manager_cond = manager_cond & (~UserModel.roles.any(Role.role_name.in_(["Admin", "CFO", "CEO", "Finance Manager"])))
        conditions.append(manager_cond)

    if is_fin_mgr and not is_admin:
        # Finance manager can see 'Payment Requested' but NOT from Admin/CFO/CEO
        fin_cond = (ExpenseReport.status == 'Payment Requested') & (~UserModel.roles.any(Role.role_name.in_(["Admin", "CFO", "CEO"])))
        conditions.append(fin_cond)
    elif is_admin:
        # Admins/CFO can see all 'Payment Requested'
        conditions.append(ExpenseReport.status == 'Payment Requested')"""

new_cond = """    user_roles = [r.role_name for r in current_user.roles]
    is_admin = any(r in user_roles for r in ["Admin", "SuperAdmin", "CEO", "CFO"])
    is_manager = "Manager" in user_roles

    conditions = [
        ExpenseReport.employee_id == current_user.user_id,
        (ExpenseApproval.approver_id == current_user.user_id) & (ExpenseReport.status != 'Draft')
    ]

    if is_manager:
        manager_cond = (UserModel.manager_id == current_user.user_id) & (ExpenseReport.status != 'Draft')
        if not is_admin:
            manager_cond = manager_cond & (~UserModel.roles.any(Role.role_name.in_(["Admin", "CFO", "CEO", "Finance Manager"])))
        conditions.append(manager_cond)"""

content = content.replace(old_cond, new_cond)

with open("src/api/expenses.py", "w") as f:
    f.write(content)

