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
            roles.append(role)
            
        # Create 20 mock employees
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
