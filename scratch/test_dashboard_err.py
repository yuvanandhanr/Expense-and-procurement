import asyncio
from src.database.config import async_session
from src.services.dashboard_service import DashboardService

async def main():
    async with async_session() as db:
        service = DashboardService(db)
        try:
            res = await service._get_pending_approvals_count(manager_id=1)
            print("Success:", res)
        except Exception as e:
            print("Error:", repr(e))

asyncio.run(main())
