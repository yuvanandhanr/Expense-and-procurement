import asyncio
from sqlalchemy import update
from src.database.session import async_session
from src.models.expense import ExpenseReport

async def main():
    async with async_session() as db:
        # We only want to change it for closed reports that are paid, 
        # or just change all "Closed" to "Approved" since we don't use Closed for anything else?
        # Actually, "Closed" was used as the terminal status for expenses.
        stmt = update(ExpenseReport).where(ExpenseReport.status == "Closed").values(status="Approved")
        await db.execute(stmt)
        await db.commit()
        print("Updated Closed to Approved in DB")

asyncio.run(main())
