import asyncio
from src.database.session import async_session
from src.models.expense import ExpenseApproval, ExpenseReport
from sqlalchemy import select

async def main():
    async with async_session() as db:
        res = await db.execute(select(ExpenseApproval))
        approvals = res.scalars().all()
        print(f"Total ExpenseApprovals: {len(approvals)}")
        
        res_rep = await db.execute(select(ExpenseReport).where(ExpenseReport.status == 'Pending Manager Approval'))
        reports = res_rep.scalars().all()
        print(f"Total Pending Manager Approval Reports: {len(reports)}")

asyncio.run(main())
