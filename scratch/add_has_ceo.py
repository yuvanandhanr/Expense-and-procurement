with open("src/api/approvals_inbox.py", "r") as f:
    content = f.read()

content = content.replace('has_finance_mgr = "Finance Manager" in user_roles or "Finance" in user_roles',
                          'has_finance_mgr = "Finance Manager" in user_roles or "Finance" in user_roles\n    has_ceo = "CEO" in user_roles')

with open("src/api/approvals_inbox.py", "w") as f:
    f.write(content)
