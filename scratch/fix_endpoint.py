with open("frontend/src/pages/Approvals.tsx", "r") as f:
    content = f.read()

content = content.replace('if (selectedWorkflow.status === "Payment Requested" && actionType === "approve") {', 'if ((selectedWorkflow.status === "Payment Requested" || selectedWorkflow.status === "Approved for Payment") && actionType === "approve") {')

with open("frontend/src/pages/Approvals.tsx", "w") as f:
    f.write(content)
