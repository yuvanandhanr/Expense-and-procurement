import asyncio
from sqlalchemy import select
from src.database.session import async_session
from src.models.expense import ExpenseReport

async def main():
    async with async_session() as db:
        query = select(ExpenseReport.expense_report_id, ExpenseReport.status).where(ExpenseReport.status == "Approved")
        result = await db.execute(query)
        reports = result.all()
        for r in reports:
            print(f"Report {r[0]} is {r[1]}")
            
        # Also check "Approved for Payment"
        query = select(ExpenseReport.expense_report_id, ExpenseReport.status).where(ExpenseReport.status == "Approved for Payment")
        result = await db.execute(query)
        reports = result.all()
        for r in reports:
            print(f"Report {r[0]} is {r[1]}")

asyncio.run(main())
