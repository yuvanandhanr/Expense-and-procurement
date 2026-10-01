import asyncio
import os
from src.database.session import async_engine
from sqlalchemy import text

async def main():
    async with async_engine.connect() as conn:
        res = await conn.execute(text('SELECT vendor_id FROM vendors;'))
        print('Vendors:', res.fetchall())

asyncio.run(main())
