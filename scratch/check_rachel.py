import asyncio
from src.database.session import async_session
from src.models.auth import User, Role
from sqlalchemy import select

async def main():
    async with async_session() as db:
        res = await db.execute(select(User).where(User.first_name == "Rachel"))
        rachel = res.scalar_one_or_none()
        if rachel:
            print(f"Rachel roles: {[r.role_name for r in rachel.roles]}")

asyncio.run(main())
