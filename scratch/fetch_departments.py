import asyncio
from src.database.session import AsyncSessionLocal
from src.models.organization import Department
from sqlalchemy import select

async def run():
    async with AsyncSessionLocal() as session:
        res = await session.execute(select(Department.department_name))
        print([r[0] for r in res.all()])

if __name__ == "__main__":
    asyncio.run(run())
