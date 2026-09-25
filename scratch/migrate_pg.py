import asyncio
from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy import text
import os
from dotenv import load_dotenv

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")

async def migrate():
    engine = create_async_engine(DATABASE_URL)
    async with engine.begin() as conn:
        try:
            await conn.execute(
                text("ALTER TABLE asset_incidents ADD COLUMN IF NOT EXISTS manager_inspection_assessment VARCHAR(100);")
            )
        except Exception as e:
            print(e)
            
        try:
            await conn.execute(
                text("ALTER TABLE asset_incidents ADD COLUMN IF NOT EXISTS manager_inspection_comments TEXT;")
            )
        except Exception as e:
            print(e)
            
        try:
            await conn.execute(
                text("ALTER TABLE asset_incidents ADD COLUMN IF NOT EXISTS admin_inspection_resolution VARCHAR(100);")
            )
        except Exception as e:
            print(e)
            
        try:
            await conn.execute(
                text("ALTER TABLE asset_incidents ADD COLUMN IF NOT EXISTS admin_comments TEXT;")
            )
        except Exception as e:
            print(e)
            
        try:
            await conn.execute(
                text("ALTER TABLE asset_incidents ADD COLUMN IF NOT EXISTS image_url VARCHAR(512);")
            )
        except Exception as e:
            print(e)
            
        try:
            await conn.execute(
                text("ALTER TABLE asset_incidents ADD COLUMN IF NOT EXISTS physical_inspection_done BOOLEAN DEFAULT FALSE;")
            )
        except Exception as e:
            print(e)
            
        print("Migration complete!")
    await engine.dispose()

asyncio.run(migrate())
