import asyncio
from src.database.dependency import get_db_session
from src.schemas.auth import CurrentUser
from src.services.auth_service import UserService

async def main():
    async for db in get_db_session():
        try:
            service = UserService(db)
            users = await service.user_repo.list_all()
            user = await service.get_user(users[0].user_id)
            user.is_locked = True
            await service.user_repo.update(user)
            await db.commit()
            await db.refresh(user)
            
            # Now try to validate with Pydantic
            CurrentUser.model_validate(user)
            print("Successfully validated")
            
            # Reset
            user.is_locked = False
            await service.user_repo.update(user)
            await db.commit()
        except Exception as e:
            print("Error:", repr(e))
            import traceback
            traceback.print_exc()
        break

asyncio.run(main())
