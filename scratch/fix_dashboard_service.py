with open("src/services/dashboard_service.py", "r") as f:
    content = f.read()

content = content.replace(
    'ExpenseReport.status.in_(["Approved", "Finance Verified", "Payment Requested", "Closed"])',
    'ExpenseReport.status.in_(["Finance Verified", "Payment Requested", "Closed"])'
)

with open("src/services/dashboard_service.py", "w") as f:
    f.write(content)
