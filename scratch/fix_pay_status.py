with open("src/api/expenses.py", "r") as f:
    content = f.read()

content = content.replace(
    'if report.status != "Payment Requested":',
    'if report.status not in ["Payment Requested", "Approved for Payment"]:'
)

with open("src/api/expenses.py", "w") as f:
    f.write(content)
