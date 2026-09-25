import asyncio
from sqlalchemy import update
from src.database.session import async_session
from src.models.expense import ExpenseReport

async def main():
    async with async_session() as db:
        stmt = update(ExpenseReport).where(ExpenseReport.status == "Approved").values(status="Closed")
        await db.execute(stmt)
        await db.commit()
        print("Updated Approved to Closed in DB")

asyncio.run(main())
