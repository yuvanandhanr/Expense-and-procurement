with open("src/api/expenses.py", "r") as f:
    content = f.read()

# in authorize_payment endpoint
content = content.replace('report.status = "Closed"\n    report.payment_status = "Paid"', 'report.status = "Approved"\n    report.payment_status = "Paid"')

# in `_can_access_report`
content = content.replace('["Pending Manager Approval", "Pending Finance Manager Approval", "Payment Requested", "Approved for Payment", "Finance Rejected", "Closed"]', '["Pending Manager Approval", "Pending Finance Manager Approval", "Payment Requested", "Approved for Payment", "Finance Rejected", "Approved"]')

with open("src/api/expenses.py", "w") as f:
    f.write(content)
