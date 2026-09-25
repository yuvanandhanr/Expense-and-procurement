import asyncio
from src.database.session import async_session
from src.models.auth import User
from sqlalchemy import select

async def main():
    async with async_session() as db:
        res = await db.execute(select(User).where(User.first_name.ilike('%Rachel%')))
        rachels = res.scalars().all()
        for r in rachels:
            print(f"Rachel: {r.email} - {r.first_name} {r.last_name}")

asyncio.run(main())
