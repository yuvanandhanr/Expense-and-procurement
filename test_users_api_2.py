import asyncio
from src.database.session import async_session
from src.services.auth_service import UserService

async def test():
    async with async_session() as db:
        service = UserService(db)
        try:
            users = await service.list_users()
            print(f"Success! Found {len(users)} users.")
        except Exception as e:
            import traceback
            traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test())
