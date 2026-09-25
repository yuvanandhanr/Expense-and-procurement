with open("src/services/approval_service.py", "r") as f:
    content = f.read()

import re

old_logic = """        # Step 1: Manager Approval (Skip if requestor is CEO or has no manager)
        if manager_id and manager_id != pr.requestor_id and not requestor_is_ceo:
            steps_to_create.append({"step_number": step_counter, "approver_role_id": manager_role_id, "approver_id": manager_id})
            step_counter += 1"""

new_logic = """        # Step 1: Manager Approval (Only for regular employees, skip for managers and above)
        requestor_is_higher_level = False
        if requestor:
            requestor_is_higher_level = any(r.role_name in ["Manager", "Finance Manager", "CFO", "CEO", "Admin", "SuperAdmin", "Finance"] for r in requestor.roles)
            
        if manager_id and manager_id != pr.requestor_id and not requestor_is_higher_level:
            steps_to_create.append({"step_number": step_counter, "approver_role_id": manager_role_id, "approver_id": manager_id})
            step_counter += 1"""

content = content.replace(old_logic, new_logic)

with open("src/services/approval_service.py", "w") as f:
    f.write(content)
