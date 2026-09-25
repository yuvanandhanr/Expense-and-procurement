with open("src/api/approvals_inbox.py", "r") as f:
    content = f.read()

content = content.replace(
    ".join(ExpenseApproval, (ExpenseApproval.expense_report_id == ExpenseReport.expense_report_id))",
    ".outerjoin(ExpenseApproval, (ExpenseApproval.expense_report_id == ExpenseReport.expense_report_id) & (ExpenseApproval.status == \"Pending\"))"
)

with open("src/api/approvals_inbox.py", "w") as f:
    f.write(content)
