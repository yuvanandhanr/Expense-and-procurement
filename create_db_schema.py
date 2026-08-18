import asyncio
from src.database.database import async_engine
# The project might define Base in src.database.database or src.models
# We should import all models so that they are registered in the Base metadata
from src.database.base import Base
# Import all models to ensure they are attached to Base.metadata
import src.models
# We might need to import more models if they exist, but let's try this first
# Actually, the project probably has a central models module or imports everything in src/main.py

async def init_db():
    print("Creating tables...")
    async with async_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    print("Tables created.")

if __name__ == "__main__":
    asyncio.run(init_db())
