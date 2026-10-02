import asyncio
from src.database.dependency import get_db_session
from src.api.users import lock_user

async def main():
    async for db in get_db_session():
        try:
            from src.services.auth_service import UserService
            service = UserService(db)
            users = await service.user_repo.list_all()
            if not users:
                print("No users found.")
                return
            admin_user = next((u for u in users if any(r.role_name == "Admin" for r in u.roles)), None)
            if not admin_user:
                print("No admin user found.")
                return
            target_user = users[0]
            
            # Call the endpoint directly
            print("Calling lock_user...")
            res = await lock_user(user_id=target_user.user_id, db=db, current_user=admin_user)
            print("Success:", res)
        except Exception as e:
            print("Error inside lock_user:", repr(e))
            import traceback
            traceback.print_exc()
        finally:
            # Revert lock
            if target_user:
                target_user.is_locked = False
                await service.user_repo.update(target_user)
                await db.commit()
        break

asyncio.run(main())
