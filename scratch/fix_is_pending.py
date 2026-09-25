with open("frontend/src/pages/Approvals.tsx", "r") as f:
    content = f.read()

content = content.replace('const isPaymentRequested = s === "Payment Requested";', 'const isPaymentRequested = s === "Payment Requested" || s === "Approved for Payment";')

with open("frontend/src/pages/Approvals.tsx", "w") as f:
    f.write(content)
