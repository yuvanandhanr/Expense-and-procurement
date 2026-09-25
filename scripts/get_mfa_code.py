import asyncio
import pyotp
from src.core.config import settings
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from sqlalchemy import select
from src.models.vendor import Vendor

engine = create_async_engine(settings.DATABASE_URL)
async_session = sessionmaker(engine, class_=AsyncSession)

async def run():
    async with async_session() as s:
        res = await s.execute(select(Vendor).where(Vendor.mfa_secret.is_not(None)))
        vendors = res.scalars().all()
        for v in vendors:
            totp = pyotp.TOTP(v.mfa_secret)
            print(f"Vendor: {v.email} - Code: {totp.now()}")

asyncio.run(run())
