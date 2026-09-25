import asyncio
from src.database.session import async_session
from src.models.auth import User
from sqlalchemy import select

async def main():
    async with async_session() as db:
        res = await db.execute(select(User).where(User.first_name == "Rachel"))
        r = res.scalar_one_or_none()
        if r:
            print(f"Rachel designation: {r.designation}")

asyncio.run(main())
