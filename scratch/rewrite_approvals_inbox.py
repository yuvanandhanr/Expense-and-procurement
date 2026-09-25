import re

with open("/Users/a.chaitnasree/Expense-and-procurement/src/api/approvals_inbox.py", "r") as f:
    content = f.read()

# Replace "Reported" with "Submitted" and "Pending Fulfillment" with "Manager Approved" and "Admin Approved"
content = content.replace('statuses.append("Reported")', 'statuses.append("Submitted")')
content = content.replace('statuses.append("Pending Fulfillment")', 'statuses.append("Manager Approved")\n            statuses.append("Admin Approved")')
content = content.replace('incident.status == "Reported"', 'incident.status == "Submitted"')

with open("/Users/a.chaitnasree/Expense-and-procurement/src/api/approvals_inbox.py", "w") as f:
    f.write(content)
