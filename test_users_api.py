import asyncio
from src.database.session import AsyncSessionLocal
from src.services.auth_service import UserService

async def test():
    async with AsyncSessionLocal() as db:
        service = UserService(db)
        try:
            users = await service.list_users()
            print(f"Success! Found {len(users)} users.")
        except Exception as e:
            import traceback
            traceback.print_exc()

asyncio.run(test())
