import asyncio
from src.database.session import async_session
from src.models.auth import User
from src.models.expense import ExpenseReport
from sqlalchemy import select

async def main():
    async with async_session() as db:
        res = await db.execute(select(User).where(User.first_name == "Rachel"))
        rachel = res.scalar_one_or_none()
        
        res_rep = await db.execute(select(ExpenseReport).where(ExpenseReport.employee_id == rachel.user_id))
        reports = res_rep.scalars().all()
        for r in reports:
            print(f"Report {r.expense_report_id}: {r.status}")

asyncio.run(main())
