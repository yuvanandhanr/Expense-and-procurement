import asyncio
from src.database.dependency import get_db_session
from src.schemas.auth import CurrentUser
from src.services.auth_service import UserService

async def main():
    async for db in get_db_session():
        try:
            service = UserService(db)
            users = await service.user_repo.list_all()
            if users:
                user = users[0]
                # Pydantic validation
                user_schema = CurrentUser.model_validate(user)
                print("Serialization successful")
        except Exception as e:
            print("Error during serialization:", repr(e))
            import traceback
            traceback.print_exc()
        break

asyncio.run(main())
