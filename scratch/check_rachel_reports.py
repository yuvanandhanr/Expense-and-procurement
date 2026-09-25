import asyncio
from src.database.session import async_session
from src.models.auth import User, Role
from src.models.expense import ExpenseReport
from sqlalchemy import select

async def main():
    async with async_session() as db:
        res = await db.execute(select(User).where(User.first_name == "Rachel"))
        rachel = res.scalar_one_or_none()
        if not rachel:
            print("Rachel not found")
            return
            
        print("Rachel user_id:", rachel.user_id)
        
        # Check her direct reports
        res = await db.execute(select(User).where(User.manager_id == rachel.user_id))
        reports = res.scalars().all()
        print("Direct reports:", [u.email for u in reports])
        
        # Check expenses for those reports
        report_ids = [u.user_id for u in reports]
        if report_ids:
            res = await db.execute(select(ExpenseReport).where(ExpenseReport.employee_id.in_(report_ids)))
            expenses = res.scalars().all()
            print("Expenses for reports:", [(e.expense_report_id, e.status) for e in expenses])

asyncio.run(main())
