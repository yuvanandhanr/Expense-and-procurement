import asyncio
from src.database.session import async_session
from src.models.auth import User
from sqlalchemy import select

async def main():
    async with async_session() as db:
        res = await db.execute(select(User).where(User.first_name == "Rachel"))
        rachel = res.scalar_one_or_none()
        
        res = await db.execute(select(User).where(User.first_name == "David", User.last_name == "Kim"))
        david = res.scalar_one_or_none()
        
        if rachel and david:
            rachel.manager_id = david.user_id
            await db.commit()
            print("Assigned David Kim as Rachel's manager!")

asyncio.run(main())
