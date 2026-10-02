import asyncio
from src.database.dependency import get_db_session
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from src.models.assets import Asset
from src.api.assets import resolve_category_name

async def main():
    async for db in get_db_session():
        stmt = select(Asset).options(selectinload(Asset.category))
        res = await db.execute(stmt)
        for a in res.scalars():
            cat_name = resolve_category_name(a)
            print(f"Asset: {a.asset_tag}, Category ID: {a.category_id}, Resolved Cat: {cat_name}")
        break

asyncio.run(main())
