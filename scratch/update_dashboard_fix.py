import re

with open("src/services/dashboard_service.py", "r") as f:
    content = f.read()

old_pending = """        if manager_id:
            user = await self.db.get(User, manager_id)
            if user:
                user_roles = [r.role_id for r in user.roles]"""

new_pending = """        if manager_id:
            from sqlalchemy import select
            from sqlalchemy.orm import selectinload
            result = await self.db.execute(select(User).options(selectinload(User.roles)).where(User.user_id == manager_id))
            user = result.scalar_one_or_none()
            if user:
                user_roles = [r.role_id for r in user.roles]"""

content = content.replace(old_pending, new_pending)

with open("src/services/dashboard_service.py", "w") as f:
    f.write(content)
