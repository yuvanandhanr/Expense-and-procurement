import asyncio
from sqlalchemy.ext.asyncio import AsyncSession
from src.database.session import async_session
from src.services.approval_service import ApprovalService
from src.models.auth import User
from sqlalchemy import select
from sqlalchemy.orm import selectinload

async def test_approvals():
    async with async_session() as db:
        result = await db.execute(select(User).options(selectinload(User.roles)))
        users = result.scalars().all()
        service = ApprovalService(db)
        for user in users:
            try:
                workflows = await service.get_pending_approvals_for_user(user)
                print(f"User {user.email}: Success, found {len(workflows)} workflows")
            except Exception as e:
                import traceback
                print(f"User {user.email} failed:")
                traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_approvals())
