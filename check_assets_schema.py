import asyncio
from sqlalchemy import text
from src.database.dependency import get_db_session

async def main():
    async for db in get_db_session():
        try:
            result = await db.execute(text("""
                SELECT column_name, data_type, is_nullable
                FROM information_schema.columns
                WHERE table_name = 'assets';
            """))
            for row in result:
                print(row)
        except Exception as e:
            print(repr(e))
        break

asyncio.run(main())
