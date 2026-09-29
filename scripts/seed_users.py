import asyncio
import os
import sys

# Add project root to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from sqlalchemy import select
from faker import Faker
import random

from src.core.config import settings
from src.models.auth import User, Role
from src.services.auth_service import PasswordHelper

fake = Faker()

# IMPORTANT: Update this list with your real team members' details
REAL_USERS = [
    {"email": "c.anisetty@dataeko.ai", "first_name": "Chaitna Sree", "last_name": "Anisetty", "role": "Employee"},
    {"email": "s.verma@dataeko.ai", "first_name": "Sumit", "last_name": "Verma", "role": "Employee"},
    {"email": "y.raja@dataeko.ai", "first_name": "Yuvanandan", "last_name": "Raja", "role": "Employee"},
]

async def seed_users():
    engine = create_async_engine(settings.DATABASE_URL, echo=False)
    async_session = sessionmaker(engine, expire_on_commit=False, class_=AsyncSession)
    
    async with async_session() as session:
        # Get roles
        roles = []
        for role_name in ["Admin", "Manager", "Finance Manager", "CFO", "Employee", "Vendor Portal"]:
            result = await session.execute(select(Role).where(Role.role_name == role_name))
            role = result.scalar_one_or_none()
            if not role:
                role = Role(role_name=role_name, status=True)
                session.add(role)
                await session.flush()
            
            # Ensure users.view permission for executives
            if role_name in ["Manager", "Finance Manager", "CFO", "CEO"]:
                result_perm = await session.execute(select(Permission).where(Permission.permission_name == "users.view"))
                perm = result_perm.scalar_one_or_none()
                if not perm:
                    perm = Permission(permission_name="users.view", description="View users")
                    session.add(perm)
                    await session.flush()
                has_perm = any(p.permission_name == "users.view" for p in role.permissions)
                if not has_perm:
                    role.permissions.append(perm)
                    
            roles.append(role)
            
        # Create real users first
        print("Seeding real users...")
        for ru in REAL_USERS:
            # Check if exists
            result = await session.execute(select(User).where(User.email == ru["email"]))
            if result.scalar_one_or_none():
                continue
                
            # Find the assigned role
            assigned_role = next((r for r in roles if r.role_name == ru["role"]), roles[0])
            
            user = User(
                employee_code=f"REAL-{fake.random_int(min=1000, max=9999)}",
                first_name=ru["first_name"],
                last_name=ru["last_name"],
                email=ru["email"],
                login_provider="GOOGLE",
                status="Active",
                password_hash=PasswordHelper.hash_password("Password@123")
            )
            user.roles.append(assigned_role)
            session.add(user)
        
        # Create 20 mock employees for testing
        print("Seeding demo/mock users...")
        for i in range(20):
            first_name = fake.first_name()
            last_name = fake.last_name()
            email = f"{first_name.lower()}.{last_name.lower()}@dataeko.ai"
            
            # Check if exists
            result = await session.execute(select(User).where(User.email == email))
            if result.scalar_one_or_none():
                continue
                
            role = random.choice(roles[:-1]) # exclude vendor portal
            
            user = User(
                employee_code=f"DE-{fake.random_int(min=1000, max=9999)}",
                first_name=first_name,
                last_name=last_name,
                email=email,
                login_provider="GOOGLE",
                status="Active",
                password_hash=PasswordHelper.hash_password("Password@123")
            )
            user.roles.append(role)
            session.add(user)
            
        await session.commit()
        print("Successfully seeded 20 mock employees.")

if __name__ == "__main__":
    asyncio.run(seed_users())
