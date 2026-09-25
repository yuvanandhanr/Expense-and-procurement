import asyncio
from src.database.session import async_session
from src.models.auth import User, Role
from sqlalchemy import select

async def main():
    async with async_session() as db:
        res = await db.execute(select(User).join(User.roles).where(Role.role_name == "Finance Manager"))
        users = res.scalars().all()
        for u in users:
            print(f"FM: {u.email}")

asyncio.run(main())
