import asyncio
from src.database.dependency import get_db_session
from sqlalchemy import select, update
from src.models.assets import Asset, AssetCategory

async def main():
    async for db in get_db_session():
        # Get category_id for Laptop
        stmt = select(AssetCategory).where(AssetCategory.category_name == "Laptop")
        cat = (await db.execute(stmt)).scalar_one_or_none()
        if not cat:
            print("Laptop category not found")
            return
        
        # Update asset F2Y4H69GP
        stmt = update(Asset).where(Asset.asset_tag == "F2Y4H69GP").values(category_id=cat.category_id)
        await db.execute(stmt)
        await db.commit()
        print("Updated F2Y4H69GP to Laptop!")
        break

asyncio.run(main())
