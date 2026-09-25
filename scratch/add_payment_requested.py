import re

with open("src/api/approvals_inbox.py", "r") as f:
    content = f.read()

old_exp_q = """        stmt = (
            select(ExpenseReport, UserModel)
            .options(selectinload(UserModel.roles))
            .join(UserModel, ExpenseReport.employee_id == UserModel.user_id)
            .join(ExpenseApproval, (ExpenseApproval.expense_report_id == ExpenseReport.expense_report_id))
            .where(
                ExpenseReport.employee_id != current_user.user_id,
                ExpenseReport.status != "Draft",
                ExpenseApproval.approver_id == current_user.user_id,
                ExpenseApproval.status == "Pending"
            )
        )
        
        result = await db.execute(stmt)"""

new_exp_q = """        from sqlalchemy import or_
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
        
        result = await db.execute(stmt)"""

content = content.replace(old_exp_q, new_exp_q)

with open("src/api/approvals_inbox.py", "w") as f:
    f.write(content)
