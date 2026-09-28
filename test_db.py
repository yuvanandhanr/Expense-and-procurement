import asyncio
from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy import text

async def main():
    db_url = "postgresql+asyncpg://postgres:postgres%25123@db.qagextokkrxrrmowyser.supabase.co:5432/postgres"
    engine = create_async_engine(db_url, echo=True)
    try:
        async with engine.begin() as conn:
            result = await conn.execute(text("SELECT 1;"))
            print("Connected successfully!")
    except Exception as e:
        print("Error:", e)
    finally:
        await engine.dispose()

asyncio.run(main())
