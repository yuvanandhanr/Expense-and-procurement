with open("/Users/a.chaitnasree/Expense-and-procurement/frontend/src/pages/Approvals.tsx", "r") as f:
    content = f.read()

import re
# Replace the disabled condition
content = re.sub(
    r'disabled={.*?\}',
    'disabled={isSubmitting || ((actionType === "reject" || actionType === "return") && !comment.trim()) || (selectedWorkflow?.status === "Submitted" && actionType === "approve" && selectedWorkflow?.entity_type === "AssetIncident" && !managerAssessment) || (selectedWorkflow?.status === "Manager Approved" && actionType === "approve" && selectedWorkflow?.entity_type === "AssetIncident" && !adminResolution)}',
    content
)

with open("/Users/a.chaitnasree/Expense-and-procurement/frontend/src/pages/Approvals.tsx", "w") as f:
    f.write(content)
