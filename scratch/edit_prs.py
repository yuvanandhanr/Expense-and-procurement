with open('src/api/purchase_requisitions.py', 'r') as f:
    content = f.read()

# 1. Update check_pr_access roles
old_check = 'if any(role in user_roles for role in ["Admin", "CFO", "Finance Manager", "Finance", "Manager"]):'
new_check = 'if any(role in user_roles for role in ["Admin", "CFO", "Finance Manager", "Finance", "Manager", "CEO"]):'
content = content.replace(old_check, new_check)

# 2. Update list_prs roles
old_list = 'if any(role in user_roles for role in ["Admin", "CFO", "Finance Manager", "Finance", "Procurement"]):'
new_list = 'if any(role in user_roles for role in ["Admin", "CFO", "Finance Manager", "Finance", "Procurement", "CEO"]):'
content = content.replace(old_list, new_list)

with open('src/api/purchase_requisitions.py', 'w') as f:
    f.write(content)

print("Done PRs")
