import asyncio
from src.database.database import async_engine
from src.database.session import async_session
from src.models.organization import Department, CostCenter
from sqlalchemy import select

async def seed_org():
    print("Seeding mock organization data...")
    async with async_session() as session:
        # Seed Department 123
        dept = await session.get(Department, 123)
        if not dept:
            dept = Department(department_id=123, department_name="Test Department 123", department_code="D123", status=True)
            session.add(dept)
        
        # Seed Cost Center 456
        cc = await session.get(CostCenter, 456)
        if not cc:
            cc = CostCenter(cost_center_id=456, cost_center_name="Test CC 456", department_id=123, budget_limit=100000.00, status=True)
            session.add(cc)

        await session.commit()
    print("Mock organization data seeded.")

if __name__ == "__main__":
    asyncio.run(seed_org())
