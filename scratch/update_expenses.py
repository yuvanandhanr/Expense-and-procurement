import re

with open("src/api/expenses.py", "r") as f:
    content = f.read()

old_query = """    from src.models.auth import User as UserModel

    stmt = select(ExpenseReport).options("""

new_query = """    from src.models.auth import User as UserModel, Role

    stmt = select(ExpenseReport).options("""

content = content.replace(old_query, new_query)

old_cond = """    conditions = [
        ExpenseReport.employee_id == current_user.user_id,
        (UserModel.manager_id == current_user.user_id) & (ExpenseReport.status != 'Draft'),
        (ExpenseApproval.approver_id == current_user.user_id) & (ExpenseReport.status != 'Draft')
    ]"""

new_cond = """    user_roles = [r.role_name for r in current_user.roles]
    is_pure_manager = "Manager" in user_roles and not any(r in user_roles for r in ["Admin", "SuperAdmin", "CEO", "CFO"])

    manager_cond = (UserModel.manager_id == current_user.user_id) & (ExpenseReport.status != 'Draft')
    if is_pure_manager:
        manager_cond = manager_cond & (~UserModel.roles.any(Role.role_name.in_(["Admin", "CFO", "CEO", "Finance Manager"])))

    conditions = [
        ExpenseReport.employee_id == current_user.user_id,
        manager_cond,
        (ExpenseApproval.approver_id == current_user.user_id) & (ExpenseReport.status != 'Draft')
    ]"""

content = content.replace(old_cond, new_cond)

with open("src/api/expenses.py", "w") as f:
    f.write(content)

