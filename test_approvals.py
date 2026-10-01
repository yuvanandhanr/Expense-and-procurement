import asyncio
from sqlalchemy.orm import sessionmaker, declarative_base
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from src.database import get_db_session
from src.api.approvals_inbox import _get_current_user_from_token
from src.models.auth import User
from sqlalchemy import select

async def main():
    async for db in get_db_session():
        # Get Rachel Foster (Manager)
        stmt = select(User).where(User.email == 'rachel.foster@dataeko.ai')
        result = await db.execute(stmt)
        user = result.scalar_one_or_none()
        
        # Test approvals_inbox logic directly
        from src.api.approvals_inbox import get_approvals_inbox
        res = await get_approvals_inbox(db=db, current_user=user)
        for wf in res:
            if wf['entity_type'] == 'ExpenseReport':
                print(f"Expense {wf['entity_id']}: status={wf['status']}, can_approve={wf.get('can_approve')}")
        break

asyncio.run(main())
