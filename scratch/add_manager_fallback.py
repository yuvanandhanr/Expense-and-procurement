import re

with open("src/api/approvals_inbox.py", "r") as f:
    content = f.read()

# I will add the manager fallback condition back.
old_cond = """        conditions = [ExpenseApproval.approver_id == current_user.user_id]
        
        # Finance Managers can see Payment Requested items, EXCEPT those from Admin/CEO/CFO"""

new_cond = """        conditions = [ExpenseApproval.approver_id == current_user.user_id]
        
        # Fallback for old claims without ExpenseApproval rows
        if has_manager:
            conditions.append(
                (ExpenseReport.status == "Pending Manager Approval") & 
                (UserModel.manager_id == current_user.user_id)
            )
            
        # Finance Managers can see Payment Requested items, EXCEPT those from Admin/CEO/CFO"""

content = content.replace(old_cond, new_cond)

with open("src/api/approvals_inbox.py", "w") as f:
    f.write(content)
