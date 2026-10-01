import asyncio
from src.database.dependency import get_db_session
from datetime import datetime, timezone, timedelta

async def main():
    async for db in get_db_session():
        try:
            from src.services.auth_service import UserService
            service = UserService(db)
            user = await service.get_user(7)
            
            # Using naive UTC datetime
            user.is_locked = True
            user.locked_until = datetime.now(timezone.utc).replace(tzinfo=None) + timedelta(days=365)
            await service.user_repo.update(user)
            await db.commit()
            print("Successfully updated using naive UTC datetime!")
            
            # Revert
            user.is_locked = False
            await service.user_repo.update(user)
            await db.commit()
        except Exception as e:
            print("Error:", repr(e))
            import traceback
            traceback.print_exc()
        break

asyncio.run(main())
