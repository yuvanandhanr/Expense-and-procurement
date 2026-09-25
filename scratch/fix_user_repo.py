import re

with open("src/repositories/auth.py", "r") as f:
    content = f.read()

# I want to change:
#     async def get_by_id(self, user_id: int) -> Optional[User]:
#         """
#         Retrieves a user by their integer primary key.
#         """
#         return await self.session.get(User, user_id)
# To:
#     async def get_by_id(self, user_id: int) -> Optional[User]:
#         query = select(User).options(selectinload(User.roles)).where(User.user_id == user_id)
#         result = await self.session.execute(query)
#         return result.scalar_one_or_none()

old_get_by_id = r"async def get_by_id\(self, user_id: int\) -> Optional\[User\]:.*?return await self.session.get\(User, user_id\)"

new_get_by_id = """async def get_by_id(self, user_id: int) -> Optional[User]:
        \"\"\"
        Retrieves a user by their integer primary key, eagerly loading roles.
        \"\"\"
        from sqlalchemy.orm import selectinload
        query = select(User).options(selectinload(User.roles)).where(User.user_id == user_id)
        result = await self.session.execute(query)
        return result.scalar_one_or_none()"""

content = re.sub(old_get_by_id, new_get_by_id, content, flags=re.DOTALL)

with open("src/repositories/auth.py", "w") as f:
    f.write(content)
