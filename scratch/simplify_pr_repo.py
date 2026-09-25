with open("src/repositories/purchase_requisition.py", "r") as f:
    content = f.read()

import re

old_logic = """        conditions = [self.model.requestor_id == user.user_id]
        
        # If manager, can see direct reports
        user_role_names = [r.role_name for r in user.roles]
        if "Manager" in user_role_names:
            manager_cond = (UserModel.manager_id == user.user_id) & (self.model.status != "Draft")
            if not any(r in user_role_names for r in ["Admin", "SuperAdmin", "CEO", "CFO"]):
                manager_cond = manager_cond & (~UserModel.roles.any(Role.role_name.in_(["Admin", "CFO", "CEO", "Finance Manager"])))
            conditions.append(manager_cond)
            
        # In approval step or history
        conditions.append((ApprovalStep.approver_id == user.user_id) & (self.model.status != "Draft"))
        conditions.append((ApprovalStep.approver_id.is_(None)) & (ApprovalStep.approver_role_id.in_(user_roles)) & (self.model.status != "Draft"))
        
        if "Admin" in user_role_names or "SuperAdmin" in user_role_names or "CFO" in user_role_names or "CEO" in user_role_names:
            conditions.append(self.model.status != "Draft")
            
        stmt = stmt.where(or_(*conditions)).order_by(self.model.created_at.desc())"""

new_logic = """        # Only show the user's own requisitions in 'My Requisitions'
        conditions = [self.model.requestor_id == user.user_id]
        
        stmt = stmt.where(or_(*conditions)).order_by(self.model.created_at.desc())"""

content = content.replace(old_logic, new_logic)

with open("src/repositories/purchase_requisition.py", "w") as f:
    f.write(content)
