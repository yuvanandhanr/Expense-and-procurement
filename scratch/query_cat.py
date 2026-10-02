import asyncio
import sys
sys.path.append("/Users/a.chaitnasree/Expense-and-procurement")
from src.database.database import async_session
from sqlalchemy import select
from src.models.assets import AssetCategory

async def main():
    async with async_session() as session:
        res = await session.execute(select(AssetCategory))
        for c in res.scalars():
            print(f"{c.category_id}: {c.category_name}")

asyncio.run(main())
