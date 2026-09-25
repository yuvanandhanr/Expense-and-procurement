with open("frontend/src/pages/Expenses.tsx", "r") as f:
    content = f.read()

# Replace "Closed" with "Approved" in the sub tabs for expenses
content = content.replace(
    '["All", "Draft", "Submitted", "Closed", "Rejected"]',
    '["All", "Draft", "Submitted", "Approved", "Rejected"]'
)

# Update the stats calculation for "Approved" instead of "Closed"
content = content.replace(
    'Closed: expenses.filter((r: any) => r.status === "Closed").length,',
    'Approved: expenses.filter((r: any) => r.status === "Approved").length,'
)

# Update the filter condition
content = content.replace(
    'if (statusFilter === "Closed") return r.status === "Closed";',
    'if (statusFilter === "Approved") return r.status === "Approved";'
)

# Also fix the logic checking for "Closed"
content = content.replace('r.status === "Closed"', 'r.status === "Approved"')
content = content.replace('report.status === "Closed"', 'report.status === "Approved"')
content = content.replace('report.status === \'Closed\'', 'report.status === \'Approved\'')
content = content.replace('["Closed", "Rejected", "Returned for Correction"]', '["Approved", "Rejected", "Returned for Correction"]')
content = content.replace('["Closed", "Payment Requested", "Finance Verified"]', '["Approved", "Payment Requested", "Finance Verified"]')

with open("frontend/src/pages/Expenses.tsx", "w") as f:
    f.write(content)
