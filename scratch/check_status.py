import asyncio
from src.database.session import async_session
from src.models.expense import ExpenseReport
from sqlalchemy import select

async def main():
    async with async_session() as db:
        res = await db.execute(select(ExpenseReport.status))
        statuses = res.scalars().all()
        from collections import Counter
        print(Counter(statuses))

asyncio.run(main())
