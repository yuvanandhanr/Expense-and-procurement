with open("src/api/approvals_inbox.py", "r") as f:
    content = f.read()

# Replace the where clause
old_where = """            .where(
                ExpenseReport.employee_id != current_user.user_id,
                ExpenseReport.status != "Draft",
                ExpenseApproval.status == "Pending"
            )"""

new_where = """            .where(
                ExpenseReport.employee_id != current_user.user_id,
                ExpenseReport.status != "Draft"
            )"""

content = content.replace(old_where, new_where)

with open("src/api/approvals_inbox.py", "w") as f:
    f.write(content)
