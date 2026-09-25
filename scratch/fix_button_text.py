with open("frontend/src/components/expenses/ReimbursementDetailModal.tsx", "r") as f:
    content = f.read()

content = content.replace(
    '{receiptDetails.status === "Payment Requested" ? "Authorize Payment" : "Approve"}',
    '{(receiptDetails.status === "Payment Requested" || receiptDetails.status === "Approved for Payment") ? "Authorize Payment" : "Approve"}'
)

content = content.replace(
    'receiptDetails.status !== "Payment Requested"',
    'receiptDetails.status !== "Payment Requested" && receiptDetails.status !== "Approved for Payment"'
)

with open("frontend/src/components/expenses/ReimbursementDetailModal.tsx", "w") as f:
    f.write(content)
