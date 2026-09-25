import asyncio
from sqlalchemy import select, update
from src.database.database import async_engine
from src.database.session import async_session
from src.models.auth import User
from src.models.expense import ExpenseApproval

async def fix_approvals():
    async with async_session() as session:
        # Find manager
        result = await session.execute(select(User).where(User.email == 'manager@dataeko.ai'))
        manager = result.scalar_one_or_none()
        
        # Find employee
        result = await session.execute(select(User).where(User.email == 'employee@dataeko.ai'))
        employee = result.scalar_one_or_none()
        
        if manager and employee:
            # Update employee manager_id
            employee.manager_id = manager.user_id
            session.add(employee)
            print(f"Updated employee manager_id to {manager.user_id}")
            
            # Update any ExpenseApproval where approver_id is None
            await session.execute(
                update(ExpenseApproval)
                .where(ExpenseApproval.approver_id.is_(None))
                .values(approver_id=manager.user_id)
            )
            print("Updated pending ExpenseApprovals.")
            
            await session.commit()
            print("Fix applied successfully.")
        else:
            print("Could not find manager or employee.")

if __name__ == "__main__":
    asyncio.run(fix_approvals())
