import re

with open("src/api/asset_incidents.py", "r") as f:
    content = f.read()

old_query = """    from sqlalchemy import select, or_
    from src.models.auth import User as UserModel"""

new_query = """    from sqlalchemy import select, or_
    from src.models.auth import User as UserModel, Role"""

content = content.replace(old_query, new_query)

old_cond = """    user_roles = [r.role_name for r in current_user.roles]
    if "Manager" in user_roles:
        conditions.append((UserModel.manager_id == current_user.user_id) & (AssetIncident.status != "Draft"))
        conditions.append((AssetIncident.status == "Reported") & (UserModel.manager_id == current_user.user_id))"""

new_cond = """    user_roles = [r.role_name for r in current_user.roles]
    if "Manager" in user_roles:
        manager_cond1 = (UserModel.manager_id == current_user.user_id) & (AssetIncident.status != "Draft")
        manager_cond2 = (AssetIncident.status == "Reported") & (UserModel.manager_id == current_user.user_id)
        
        if not any(r in user_roles for r in ["Admin", "SuperAdmin", "CEO", "CFO"]):
            manager_cond1 = manager_cond1 & (~UserModel.roles.any(Role.role_name.in_(["Admin", "CFO", "CEO", "Finance Manager"])))
            manager_cond2 = manager_cond2 & (~UserModel.roles.any(Role.role_name.in_(["Admin", "CFO", "CEO", "Finance Manager"])))
            
        conditions.append(manager_cond1)
        conditions.append(manager_cond2)"""

content = content.replace(old_cond, new_cond)

with open("src/api/asset_incidents.py", "w") as f:
    f.write(content)

