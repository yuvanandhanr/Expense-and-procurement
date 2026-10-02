import asyncio
from src.database.dependency import get_db_session
from src.api.users import lock_user
from sqlalchemy import select
from src.models.auth import User

async def main():
    async for db in get_db_session():
        try:
            result = await db.execute(select(User))
            user = result.scalars().first()
            if user:
                await lock_user(user_id=user.user_id, db=db)
                await db.commit()
                print("Success locking user")
        except Exception as e:
            print(f"Failed: {repr(e)}")
            import traceback
            traceback.print_exc()
        break

asyncio.run(main())
