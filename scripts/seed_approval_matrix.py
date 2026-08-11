import asyncio
import os
import sys

# Add the project root to the python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from src.database.session import async_session
from src.models.approval import ApprovalMatrix
from src.models.auth import Role

async def seed_approval_matrix():
    async with async_session() as db:
        # Get roles
        query = select(Role)
        result = await db.execute(query)
        roles = result.scalars().all()
        role_map = {r.role_name: r.role_id for r in roles}
        
        manager_role_id = role_map.get("Manager")
        finance_role_id = role_map.get("Finance")
        cfo_role_id = role_map.get("CFO")
        
        if not manager_role_id or not finance_role_id or not cfo_role_id:
            print(f"Required roles are missing. Manager: {manager_role_id}, Finance: {finance_role_id}, CFO: {cfo_role_id}")
            print("Please seed roles first.")
            return

        # Clear existing matrix
        query = select(ApprovalMatrix)
        result = await db.execute(query)
        existing = result.scalars().all()
        for e in existing:
            await db.delete(e)
        await db.commit()
        
        # We need Manager for all PRs (0 to infinity)
        # We need Finance for PRs > 500 (500.01 to infinity)
        # We need CFO for PRs > 5000 (5000.01 to infinity)
        # By setting overlapping ranges, a PR of 6000 will match all three rules,
        # resulting in a 3-step workflow.

        rules = [
            ApprovalMatrix(min_amount=0, max_amount=999999999.99, approval_level=1, role_id=manager_role_id),
            ApprovalMatrix(min_amount=500.01, max_amount=999999999.99, approval_level=2, role_id=finance_role_id),
            ApprovalMatrix(min_amount=5000.01, max_amount=999999999.99, approval_level=3, role_id=cfo_role_id),
        ]
        
        db.add_all(rules)
        await db.commit()
        print("Approval Matrix seeded successfully!")

if __name__ == "__main__":
    asyncio.run(seed_approval_matrix())
