import asyncio
from sqlalchemy.ext.asyncio import AsyncSession
from src.database.session import async_session
from src.models.auth import User
from src.services.approval_service import ApprovalService
from sqlalchemy import select

async def main():
    async with async_session() as db:
        # Get users for Manager, Finance, CFO, CEO
        roles = ["Manager", "Finance", "CFO", "CEO"]
        service = ApprovalService(db)
        
        for role_name in roles:
            query = select(User).where(User.roles.any(role_name=role_name))
            result = await db.execute(query)
            user = result.scalars().first()
            if not user:
                print(f"No {role_name} found")
                continue
            
            workflows = await service.get_pending_approvals_for_user(user)
            print(f"Pending workflows for {role_name} ({user.first_name} {user.last_name}): {len(workflows)}")
            for wf in workflows:
                print(f"- PR {wf['entity_id']} Step {wf['current_step_sequence']}")

if __name__ == "__main__":
    asyncio.run(main())
