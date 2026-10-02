import asyncio
from sqlalchemy import text
from src.database.dependency import get_db_session

async def main():
    async for db in get_db_session():
        try:
            result = await db.execute(text("SELECT category_id, category_name FROM asset_categories"))
            cats = result.fetchall()
            for c in cats:
                print(c)
        except Exception as e:
            print("Error:", repr(e))
        break
asyncio.run(main())
