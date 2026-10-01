import asyncio
from src.database.dependency import get_db_session
from sqlalchemy import select
from src.models.assets import AssetCategory

async def main():
    async for db in get_db_session():
        res = await db.execute(select(AssetCategory))
        for c in res.scalars():
            print(c.category_id, c.category_name)
        break

asyncio.run(main())
