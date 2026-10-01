import asyncio
from httpx import AsyncClient
from src.main import app

async def main():
    async with AsyncClient(app=app, base_url="http://testserver") as client:
        # Mock auth dependency
        app.dependency_overrides = {} # Can't mock easily without touching deps
        pass

asyncio.run(main())
