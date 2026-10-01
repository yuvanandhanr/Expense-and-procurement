import asyncio
from src.database.dependency import get_db_session
from src.api.assets import create_asset
from src.schemas.assets import AssetCreate
from src.services.auth_service import UserService

async def main():
    async for db in get_db_session():
        try:
            service = UserService(db)
            users = await service.user_repo.list_all()
            admin = next((u for u in users if any(r.role_name == "Admin" for r in u.roles)), None)
            
            payload = AssetCreate(
                asset_number="F2Y4H69GP",
                asset_tag="F2Y4H69GP",
                model="MacBook Neo",
                category_id=6,
                cost=69000,
                status="Unassigned"
            )
            
            res = await create_asset(payload, db, admin)
            print("Successfully created!", res.asset_id)
            
            await db.delete(res)
            await db.commit()
        except Exception as e:
            print("Error occurred!")
            import traceback
            traceback.print_exc()
        break

asyncio.run(main())
