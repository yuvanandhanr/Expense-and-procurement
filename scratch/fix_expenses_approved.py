with open("frontend/src/pages/Expenses.tsx", "r") as f:
    content = f.read()

# Replace "Approved" with "Closed" in the sub tabs for expenses
content = content.replace(
    '["All", "Draft", "Submitted", "Approved", "Rejected"]',
    '["All", "Draft", "Submitted", "Closed", "Rejected"]'
)

# Update the stats calculation for "Closed" instead of "Approved"
content = content.replace(
    'Approved: expenses.filter((r: any) => r.status === "Approved" || r.status === "Closed").length,',
    'Closed: expenses.filter((r: any) => r.status === "Closed").length,'
)

# Update the filter condition
content = content.replace(
    'if (statusFilter === "Approved") return r.status === "Approved" || r.status === "Closed";',
    'if (statusFilter === "Closed") return r.status === "Closed";'
)

# Also fix the logic checking for "Approved" (even though DB has been updated, good to clean up)
content = content.replace('r.status === "Approved" || r.status === "Closed"', 'r.status === "Closed"')
content = content.replace('report.status === "Approved" || report.status === "Closed"', 'report.status === "Closed"')
content = content.replace('report.status === \'Approved\' || report.status === \'Closed\'', 'report.status === \'Closed\'')
content = content.replace('["Approved", "Closed", "Rejected", "Returned for Correction"]', '["Closed", "Rejected", "Returned for Correction"]')
content = content.replace('["Approved", "Closed", "Payment Requested", "Finance Verified"]', '["Closed", "Payment Requested", "Finance Verified"]')

with open("frontend/src/pages/Expenses.tsx", "w") as f:
    f.write(content)
