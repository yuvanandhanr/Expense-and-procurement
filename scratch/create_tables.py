import asyncio
import sys
import os

# Adjust path to include root directory
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from src.database.session import async_engine
from src.database.base import Base
import src.models

async def create_tables():
    print("Initializing database tables...")
    async with async_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    print("Tables created successfully!")

if __name__ == "__main__":
    asyncio.run(create_tables())
