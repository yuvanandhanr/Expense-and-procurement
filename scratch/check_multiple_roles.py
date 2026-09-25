import asyncio
from src.database.session import async_session
from src.models.auth import User
from sqlalchemy import select

async def main():
    async with async_session() as db:
        res = await db.execute(select(User))
        users = res.scalars().all()
        for u in users:
            roles = [r.role_name for r in u.roles]
            if len(roles) > 1:
                print(f"{u.email} roles: {roles}")
            elif len(roles) == 1 and roles[0] == "Finance Manager":
                print(f"{u.email} is purely Finance Manager")

asyncio.run(main())
