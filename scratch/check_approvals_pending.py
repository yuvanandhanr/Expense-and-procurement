import asyncio
from src.database.session import async_session
from src.models.expense import ExpenseApproval, ExpenseReport
from sqlalchemy import select

async def main():
    async with async_session() as db:
        res = await db.execute(select(ExpenseApproval).where(ExpenseApproval.status == "Pending"))
        approvals = res.scalars().all()
        for a in approvals:
            print(f"Approval {a.approval_id} for Report {a.expense_report_id} assigned to {a.approver_id}")

asyncio.run(main())
