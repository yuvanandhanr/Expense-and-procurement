import asyncio
import sys
import os
from sqlalchemy import select

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from src.database.session import async_session
from src.models.auth import Role
from src.models.organization import Department, Designation, CostCenter

async def seed():
    async with async_session() as session:
        # 1. Seed Roles
        roles_to_seed = [
            ("Admin", "Full system administrator access"),
            ("Employee", "Standard corporate employee access"),
            ("Chief", "Executive level decision-making authority"),
            ("Vendor", "External supplier partner portal access"),
            ("Manager", "Departmental purchase requisition reviewer"),
            ("Finance", "Finance reviewer and invoice processor"),
            ("CFO", "Chief Financial Officer approval authority"),
            ("CEO", "Chief Executive Officer approval authority"),
            ("Procurement", "Purchasing agent and RFQ manager")
        ]
        
        for name, desc in roles_to_seed:
            res = await session.execute(select(Role).where(Role.role_name == name))
            if not res.scalar_one_or_none():
                session.add(Role(role_name=name, status=True, description=desc))
                print(f"Seeded role: {name}")

        # 2. Seed Departments
        depts_to_seed = ["Finance", "Procurement", "HR", "Engineering", "Executive"]
        for dept_name in depts_to_seed:
            res = await session.execute(select(Department).where(Department.department_name == dept_name))
            if not res.scalar_one_or_none():
                session.add(Department(department_name=dept_name, department_code=dept_name[:3].upper(), status=True))
                print(f"Seeded department: {dept_name}")

        # 3. Seed Designations
        desigs_to_seed = ["CEO", "CFO", "Chief Procurement Officer", "Director", "Manager", "Senior Engineer"]
        for desig_name in desigs_to_seed:
            res = await session.execute(select(Designation).where(Designation.designation_name == desig_name))
            if not res.scalar_one_or_none():
                session.add(Designation(designation_name=desig_name, status=True))
                print(f"Seeded designation: {desig_name}")

        # 4. Seed Cost Centers
        ccs_to_seed = [
            "Corporate Headquarters",
            "Engineering & R&D",
            "Finance Operations"
        ]
        for name in ccs_to_seed:
            res = await session.execute(select(CostCenter).where(CostCenter.cost_center_name == name))
            if not res.scalar_one_or_none():
                session.add(CostCenter(cost_center_name=name, budget_limit=1000000.0, status=True))
                print(f"Seeded cost center: {name}")

        await session.commit()
        print("RBAC Database seed complete!")

if __name__ == "__main__":
    asyncio.run(seed())
