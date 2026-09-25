with open("src/api/approvals_inbox.py", "r") as f:
    content = f.read()

content = content.replace(
    'ExpenseReport.status.in_(["Pending Manager Approval", "Pending Finance Manager Approval", "Payment Requested", "Approved for Payment", "Finance Rejected", "Closed"])',
    'ExpenseReport.status.in_(["Pending Manager Approval", "Pending Finance Manager Approval", "Payment Requested", "Approved for Payment", "Finance Rejected", "Approved"])'
)

with open("src/api/approvals_inbox.py", "w") as f:
    f.write(content)
