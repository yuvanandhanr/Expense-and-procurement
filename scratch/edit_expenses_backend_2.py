import re

with open('src/api/expenses.py', 'r') as f:
    content = f.read()

# 1. Update _can_access_report
old_access = 'or bool(roles & {"Admin", "Finance", "Finance Manager", "CFO"})'
new_access = 'or bool(roles & {"Admin", "Finance", "Finance Manager", "CFO", "CEO"})'
content = content.replace(old_access, new_access)

# 2. Update submit_report
old_submit = 'report.status = "Pending Manager Approval"'
new_submit = 'report.status = "Corrected Claim" if report.status == "Returned for Correction" else "Pending Manager Approval"'
content = content.replace(old_submit, new_submit)

# 3. Update approve_expense
old_approve_check1 = 'if report.status not in ["Pending Manager Approval", "Pending Finance Manager Approval"]:'
new_approve_check1 = 'if report.status not in ["Pending Manager Approval", "Pending Finance Manager Approval", "Corrected Claim"]:'
content = content.replace(old_approve_check1, new_approve_check1)

old_approve_check2 = 'if report.status == "Pending Manager Approval":'
new_approve_check2 = 'if report.status in ["Pending Manager Approval", "Corrected Claim"]:'
content = content.replace(old_approve_check2, new_approve_check2)

# 4. Update reject_expense and return_expense
old_reject_return_check = 'if report.status not in ["Pending Manager Approval", "Pending Finance Manager Approval"]:'
new_reject_return_check = 'if report.status not in ["Pending Manager Approval", "Pending Finance Manager Approval", "Corrected Claim"]:'
content = content.replace(old_reject_return_check, new_reject_return_check)

with open('src/api/expenses.py', 'w') as f:
    f.write(content)

print("Done expenses.py")
