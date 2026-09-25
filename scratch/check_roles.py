import asyncio
from src.database.config import SessionLocal
from src.repositories.auth import UserRepository

async def main():
    async with SessionLocal() as db:
        repo = UserRepository(db)
        user = await repo.get_by_id(4) # David Kim, Finance Manager
        try:
            print(user.roles)
        except Exception as e:
            print("Error accessing roles:", type(e))

asyncio.run(main())
