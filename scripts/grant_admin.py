import asyncio
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from sqlalchemy import select
import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.core.config import settings
from src.models.auth import User, Role

async def grant_admin(email: str):
    engine = create_async_engine(settings.DATABASE_URL, echo=False)
    async_session = sessionmaker(engine, expire_on_commit=False, class_=AsyncSession)
    
    async with async_session() as session:
        # Find user
        stmt = select(User).where(User.email == email)
        result = await session.execute(stmt)
        user = result.scalar_one_or_none()
        if not user:
            print(f"User {email} not found.")
            return
            
        # Find Admin role
        stmt_role = select(Role).where(Role.role_name == "Admin")
        result_role = await session.execute(stmt_role)
        admin_role = result_role.scalar_one_or_none()
        
        if not admin_role:
            print("Admin role not found. Creating it...")
            admin_role = Role(role_name="Admin", status=True)
            session.add(admin_role)
            await session.flush()
            
        # Add role to user if not present
        await session.refresh(user, ['roles'])
        if admin_role not in user.roles:
            user.roles.append(admin_role)
            await session.commit()
            print(f"Granted Admin role to {email}.")
        else:
            print(f"{email} already has Admin role.")

if __name__ == "__main__":
    asyncio.run(grant_admin("y.raja@dataeko.ai"))
