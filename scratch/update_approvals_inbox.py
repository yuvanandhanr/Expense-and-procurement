import re

with open("src/api/approvals_inbox.py", "r") as f:
    content = f.read()

# 1. Add selectinload for receipts
# find `.options(selectinload(UserModel.roles))` inside ExpenseReport block
# and replace it with `.options(selectinload(UserModel.roles), selectinload(ExpenseReport.receipts))`
old_options = r"\.options\(selectinload\(UserModel\.roles\)\)\s+\.join\(UserModel, ExpenseReport\.employee_id == UserModel\.user_id\)"
new_options = """.options(selectinload(UserModel.roles), selectinload(ExpenseReport.receipts))
            .join(UserModel, ExpenseReport.employee_id == UserModel.user_id)"""

content = re.sub(old_options, new_options, content)

# 2. Update role visibility rules
# Old block:
#         if has_finance_mgr:
#             # Finance Manager sees claims they are involved in, plus legacy claims that reached them
#             conditions.append(
#                 ExpenseReport.status.in_(["Payment Requested", "Approved for Payment", "Finance Rejected", "Closed"]) & 
#                 (~UserModel.roles.any(Role.role_name.in_(["Admin", "CEO", "CFO", "SuperAdmin"])))
#             )
#             
#         if has_admin or has_cfo:
#             conditions.append(ExpenseReport.status.in_(["Payment Requested", "Approved for Payment", "Finance Rejected", "Closed", "Pending Admin Approval", "Pending CFO Approval"]))

# Note: has_ceo is missing. I need to make sure I add has_ceo.
ceo_check = r"has_finance_mgr = \"Finance Manager\" in user_roles or \"Finance\" in user_roles"
if "has_ceo = \"CEO\" in user_roles" not in content:
    content = content.replace(ceo_check, ceo_check + "\n    has_ceo = \"CEO\" in user_roles")

old_finance_mgr = r"if has_finance_mgr:\n\s+# Finance Manager sees claims they are involved in, plus legacy claims that reached them\n\s+conditions.append\(\n\s+ExpenseReport.status.in_\(\[\"Payment Requested\", \"Approved for Payment\", \"Finance Rejected\", \"Closed\"\]\) &\ \n\s+\(~UserModel.roles.any\(Role.role_name.in_\(\[\"Admin\", \"CEO\", \"CFO\", \"SuperAdmin\"\]\)\)\)\n\s+\)"

new_finance_mgr = """if has_finance_mgr:
            # Finance Manager sees claims they are involved in, plus legacy claims that reached them, plus claims currently pending manager approval
            conditions.append(
                ExpenseReport.status.in_(["Pending Manager Approval", "Pending Finance Manager Approval", "Payment Requested", "Approved for Payment", "Finance Rejected", "Closed"]) & 
                (~UserModel.roles.any(Role.role_name.in_(["Admin", "CEO", "CFO", "SuperAdmin"])))
            )"""

content = re.sub(old_finance_mgr, new_finance_mgr, content, flags=re.DOTALL)

old_admin = r"if has_admin or has_cfo:\n\s+conditions.append\(ExpenseReport.status.in_\(\[\"Payment Requested\", \"Approved for Payment\", \"Finance Rejected\", \"Closed\", \"Pending Admin Approval\", \"Pending CFO Approval\"\]\)\)"
new_admin = """if has_admin or has_cfo or has_ceo:
            # They can see ALL claims
            conditions.append(ExpenseReport.status != "Draft")"""
            
content = re.sub(old_admin, new_admin, content, flags=re.DOTALL)

with open("src/api/approvals_inbox.py", "w") as f:
    f.write(content)
