import re
with open("src/api/expenses.py", "r") as f:
    content = f.read()

content = content.replace('detail="Duplicate receipt detected in this reimbursement report."', 'detail="This exact receipt has already been uploaded previously. Duplicate receipts are not allowed."')

with open("src/api/expenses.py", "w") as f:
    f.write(content)
