import asyncio
from src.core.config import settings
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from sqlalchemy import select
from src.models.auth import User, Role

engine = create_async_engine(settings.DATABASE_URL)
async_session = sessionmaker(engine, class_=AsyncSession)

async def run():
    async with async_session() as s:
        res = await s.execute(select(User).where(User.email.like('%y.raja%')))
        user = res.scalars().first()
        if user:
            print(f"User: {user.email}")
            for role in user.roles:
                print(f"Role: {role.role_name}")
        else:
            print("Not found")

asyncio.run(run())
