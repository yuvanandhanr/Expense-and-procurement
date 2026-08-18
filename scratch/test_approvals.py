import asyncio
from sqlalchemy.ext.asyncio import AsyncSession
from src.database.session import async_session
from src.models.auth import User
from src.services.approval_service import ApprovalService
from sqlalchemy import select

async def main():
    async with async_session() as db:
        # Get manager user
        query = select(User).where(User.roles.any(role_name="Manager"))
        result = await db.execute(query)
        manager = result.scalars().first()
        if not manager:
            print("No manager found")
            return
        print(f"Checking for Manager: {manager.first_name} {manager.last_name} (ID: {manager.user_id})")
        
        service = ApprovalService(db)
        workflows = await service.get_pending_approvals_for_user(manager)
        print(f"Pending workflows for Manager: {len(workflows)}")
        for wf in workflows:
            print(f"- PR {wf['entity_id']} Step {wf['current_step_sequence']}")

if __name__ == "__main__":
    asyncio.run(main())
