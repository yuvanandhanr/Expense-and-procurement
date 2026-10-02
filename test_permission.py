import asyncio
from src.database.dependency import get_db_session
from src.auth.dependencies import PermissionChecker
from src.services.auth_service import UserService

async def main():
    async for db in get_db_session():
        try:
            service = UserService(db)
            users = await service.user_repo.list_all()
            ceo = next((u for u in users if any(r.role_name == "CEO" for r in u.roles)), None)
            if not ceo:
                print("CEO not found")
                return
                
            print("CEO:", ceo.email)
            checker = PermissionChecker("users.view")
            try:
                checker(current_user=ceo)
                print("Permission granted!")
            except Exception as e:
                print("Permission denied or error:", repr(e))
        except Exception as e:
            print("Error:", repr(e))
            import traceback
            traceback.print_exc()
        break

asyncio.run(main())
