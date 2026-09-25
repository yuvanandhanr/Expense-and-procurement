with open("src/api/approvals_inbox.py", "r") as f:
    content = f.read()

import re

# We want to replace the Expense Reports query block
old_block_pattern = r"stmt = \(\s*select\(ExpenseReport, UserModel\).*?result = await db\.execute\(stmt\)"

new_block = """stmt = (
            select(ExpenseReport, UserModel)
            .options(selectinload(UserModel.roles))
            .join(UserModel, ExpenseReport.employee_id == UserModel.user_id)
            .outerjoin(ExpenseApproval, (ExpenseApproval.expense_report_id == ExpenseReport.expense_report_id))
            .where(
                ExpenseReport.employee_id != current_user.user_id,
                ExpenseReport.status != "Draft"
            )
        )
        
        conditions = [ExpenseApproval.approver_id == current_user.user_id]
        
        if has_manager:
            # Manager sees all claims from their direct reports
            conditions.append(UserModel.manager_id == current_user.user_id)
            
        if has_finance_mgr:
            # Finance Manager sees claims they are involved in, plus legacy claims that reached them
            conditions.append(
                ExpenseReport.status.in_(["Payment Requested", "Approved for Payment", "Finance Rejected", "Closed"]) & 
                (~UserModel.roles.any(Role.role_name.in_(["Admin", "CEO", "CFO", "SuperAdmin"])))
            )
            
        if has_admin or has_cfo:
            conditions.append(ExpenseReport.status.in_(["Payment Requested", "Approved for Payment", "Finance Rejected", "Closed", "Pending Admin Approval", "Pending CFO Approval"]))
            
        stmt = stmt.where(or_(*conditions))
        
        result = await db.execute(stmt)"""

content = re.sub(old_block_pattern, new_block, content, flags=re.DOTALL)

with open("src/api/approvals_inbox.py", "w") as f:
    f.write(content)
