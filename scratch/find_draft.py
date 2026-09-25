import asyncio
from sqlalchemy import select
from src.database.session import async_session
from src.models.expense import ExpenseReport

async def main():
    async with async_session() as db:
        query = select(ExpenseReport.expense_report_id).where(ExpenseReport.employee_id == 4, ExpenseReport.status == "Draft")
        result = await db.execute(query)
        print(result.scalars().all())

asyncio.run(main())
