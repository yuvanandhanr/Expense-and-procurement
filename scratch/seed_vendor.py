import asyncio
import sys
import os
from sqlalchemy import select

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from src.database.session import async_session
from src.models.vendor import Vendor

async def seed():
    async with async_session() as session:
        # 1. Seed vendor@dataeko.ai (if wanted)
        result1 = await session.execute(select(Vendor).where(Vendor.email == "vendor@dataeko.ai"))
        if not result1.scalar_one_or_none():
            session.add(Vendor(
                vendor_code="VND-DE-01",
                vendor_name="DataEko Analytics Partner",
                email="vendor@dataeko.ai",
                status="Active"
            ))

        # 2. Seed partner@external.com (non-dataeko domain)
        result2 = await session.execute(select(Vendor).where(Vendor.email == "partner@external.com"))
        if not result2.scalar_one_or_none():
            session.add(Vendor(
                vendor_code="VND-EXT-02",
                vendor_name="External Logistics Corp",
                email="partner@external.com",
                status="Active"
            ))
            
        await session.commit()
        print("Vendor database seed complete!")

if __name__ == "__main__":
    asyncio.run(seed())
