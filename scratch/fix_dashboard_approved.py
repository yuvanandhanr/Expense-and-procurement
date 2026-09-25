with open("frontend/src/pages/Dashboard.tsx", "r") as f:
    content = f.read()

content = content.replace(
    '["Approved", "Finance Verified", "Payment Requested", "Closed"]',
    '["Finance Verified", "Payment Requested", "Closed"]'
)

with open("frontend/src/pages/Dashboard.tsx", "w") as f:
    f.write(content)
