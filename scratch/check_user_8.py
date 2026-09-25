import asyncio
from src.database.session import async_session
from src.models.auth import User
from sqlalchemy import select

async def main():
    async with async_session() as db:
        res = await db.execute(select(User).where(User.user_id == 8))
        u = res.scalar_one_or_none()
        if u:
            print(f"User 8: {u.email} - {u.first_name} {u.last_name}")

asyncio.run(main())
