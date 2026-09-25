import asyncio
from sqlalchemy.future import select
from sqlalchemy.orm import selectinload
from src.database.base import async_session_maker
from src.models.auth import User
from src.models.organization import Designation

async def main():
    async with async_session_maker() as session:
        result = await session.execute(select(User).options(selectinload(User.designation_rel)))
        users = result.scalars().all()
        for u in users:
            print(f"{u.first_name} {u.last_name}: String desig: {u.designation}, Rel desig: {u.designation_rel.designation_name if u.designation_rel else 'None'}")

if __name__ == "__main__":
    asyncio.run(main())
