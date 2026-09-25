import asyncio
from src.database.session import async_session
from src.api.approvals_inbox import get_pending_approvals
from src.api.asset_incidents import list_incidents
from src.models.auth import User
from sqlalchemy.orm import selectinload
from sqlalchemy import select

async def main():
    async with async_session() as db:
        res = await db.execute(select(User).options(selectinload(User.roles)).where(User.user_id == 2))
        user = res.scalar_one()
        print(f"Testing for user: {user.email}")
        
        try:
            print("Testing get_pending_approvals...")
            res = await get_pending_approvals(db=db, current_user=user)
            print("get_pending_approvals OK:", res)
        except Exception as e:
            import traceback
            traceback.print_exc()

        try:
            print("Testing list_incidents...")
            res2 = await list_incidents(session=db, current_user=user)
            print("list_incidents OK:", res2)
        except Exception as e:
            import traceback
            traceback.print_exc()

asyncio.run(main())
