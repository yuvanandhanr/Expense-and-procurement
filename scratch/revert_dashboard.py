with open("frontend/src/pages/Dashboard.tsx", "r") as f:
    content = f.read()

content = content.replace(
    '["Finance Verified", "Payment Requested", "Closed"]',
    '["Approved", "Finance Verified", "Payment Requested"]'
)

with open("frontend/src/pages/Dashboard.tsx", "w") as f:
    f.write(content)

with open("src/services/dashboard_service.py", "r") as f:
    content = f.read()

content = content.replace(
    'ExpenseReport.status.in_(["Finance Verified", "Payment Requested", "Closed"])',
    'ExpenseReport.status.in_(["Approved", "Finance Verified", "Payment Requested"])'
)

with open("src/services/dashboard_service.py", "w") as f:
    f.write(content)
