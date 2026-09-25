import re

with open("src/api/offboarding.py", "r") as f:
    content = f.read()

# We need to add a check in trigger_offboarding
# after:
#    emp = await session.get(User, employee_id)
#    if not emp:
#        raise HTTPException(status_code=404, detail="Employee not found")

new_check = """    emp = await session.get(User, employee_id)
    if not emp:
        raise HTTPException(status_code=404, detail="Employee not found")
        
    user_roles = [r.role_name for r in current_user.roles]
    if "Manager" in user_roles and not any(r in user_roles for r in ["Admin", "SuperAdmin"]):
        # Prevent manager from offboarding higher-ups
        await session.refresh(emp, ["roles"])
        emp_roles = [r.role_name for r in emp.roles]
        if any(r in emp_roles for r in ["Admin", "SuperAdmin", "CFO", "CEO", "Finance Manager"]):
            raise HTTPException(status_code=403, detail="Manager cannot offboard executives or administrators.")
        # Optional: ensure it's their direct report
        if emp.manager_id != current_user.user_id:
            raise HTTPException(status_code=403, detail="Manager can only offboard their direct reports.")
"""

content = re.sub(
    r'    emp = await session\.get\(User, employee_id\)\n    if not emp:\n        raise HTTPException\(status_code=404, detail="Employee not found"\)',
    new_check,
    content
)

with open("src/api/offboarding.py", "w") as f:
    f.write(content)

