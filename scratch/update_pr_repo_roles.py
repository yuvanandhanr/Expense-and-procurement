import re

with open("src/repositories/purchase_requisition.py", "r") as f:
    content = f.read()

old_query = """        from src.models.auth import User as UserModel
        from sqlalchemy import select, or_"""

new_query = """        from src.models.auth import User as UserModel, Role
        from sqlalchemy import select, or_"""

content = content.replace(old_query, new_query)

old_cond = """        # If manager, can see direct reports
        if any(r.role_name == "Manager" for r in user.roles):
            conditions.append((UserModel.manager_id == user.user_id) & (self.model.status != "Draft"))"""

new_cond = """        # If manager, can see direct reports
        user_role_names = [r.role_name for r in user.roles]
        if "Manager" in user_role_names:
            manager_cond = (UserModel.manager_id == user.user_id) & (self.model.status != "Draft")
            if not any(r in user_role_names for r in ["Admin", "SuperAdmin", "CEO", "CFO"]):
                manager_cond = manager_cond & (~UserModel.roles.any(Role.role_name.in_(["Admin", "CFO", "CEO", "Finance Manager"])))
            conditions.append(manager_cond)"""

content = content.replace(old_cond, new_cond)

with open("src/repositories/purchase_requisition.py", "w") as f:
    f.write(content)

