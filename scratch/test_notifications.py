import asyncio
from src.database.dependency import get_db_session
from src.services.notification_service import NotificationService
from src.services.auth_service import UserService

async def main():
    async for db in get_db_session():
        try:
            service = NotificationService(db)
            user_service = UserService(db)
            users = await user_service.user_repo.list_all()
            admin = next((u for u in users if any(r.role_name == "Admin" for r in u.roles)), None)
            
            notifications = await service.notification_repo.list_by_user(admin.user_id, skip=0, limit=20)
            print(f"Found {len(notifications)} notifications for admin {admin.user_id}")
            for n in notifications:
                print(n.title, n.message)
        except Exception as e:
            print("Error:", e)
            import traceback
            traceback.print_exc()
        break

asyncio.run(main())
