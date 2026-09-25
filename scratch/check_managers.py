import asyncio
from src.database.session import async_session
from src.models.auth import User, Role
from sqlalchemy import select

async def main():
    async with async_session() as db:
        res = await db.execute(select(User).join(User.roles).where(Role.role_name == "Manager"))
        managers = res.scalars().all()
        for m in managers:
            print(f"Manager: {m.email} - {m.first_name} {m.last_name}")

asyncio.run(main())
