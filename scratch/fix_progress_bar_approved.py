with open("frontend/src/components/expenses/ReimbursementDetailModal.tsx", "r") as f:
    content = f.read()

# Replace "Closed" with "Approved" in the steps arrays
content = content.replace('["Draft", "Submitted", "Manager", "Finance", "Payment", "Closed"]', '["Draft", "Submitted", "Manager", "Finance", "Payment", "Approved"]')
content = content.replace('["Draft", "Submitted", "CFO", "Payment", "Closed"]', '["Draft", "Submitted", "CFO", "Payment", "Approved"]')
content = content.replace('["Draft", "Submitted", "Finance", "Payment", "Closed"]', '["Draft", "Submitted", "Finance", "Payment", "Approved"]')

# Replace indexOf("Closed") with indexOf("Approved")
content = content.replace('steps.indexOf("Closed")', 'steps.indexOf("Approved")')

with open("frontend/src/components/expenses/ReimbursementDetailModal.tsx", "w") as f:
    f.write(content)
