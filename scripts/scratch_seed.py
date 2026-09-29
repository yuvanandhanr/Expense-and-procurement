import asyncio
import os
import sys

# Add project root to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from sqlalchemy import select
from src.core.config import settings
from src.models.auth import User, Role

async def seed():
    engine = create_async_engine(settings.DATABASE_URL, echo=False)
    async_session = sessionmaker(engine, expire_on_commit=False, class_=AsyncSession)
    
    mock_users = {
        "mock_google_cfo@dataeko.ai": "CFO",
        "mock_google_manager@dataeko.ai": "Manager",
        "mock_google_finance@dataeko.ai": "Finance Manager",
        "mock_google_employee@dataeko.ai": "Employee",
        "mock_google_ceo@dataeko.ai": "CEO",
        "mock_google_y.raja@dataeko.ai": "Admin",
    }

    async with async_session() as session:
        for email, role_name in mock_users.items():
            # Get Role
            result = await session.execute(select(Role).where(Role.role_name == role_name))
            role = result.scalar_one_or_none()
            if not role:
                role = Role(role_name=role_name, status=True)
                session.add(role)
                await session.flush()
                
            from src.models.auth import Permission
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
            
            # Use raw email to save in DB since the auth_service maps it
            # wait, mock_google_cfo@dataeko.ai will be parsed as cfo@dataeko.ai in verify_google_id_token
            # So I should seed cfo@dataeko.ai in DB
            actual_email = email.replace("mock_google_", "")

            # Check User
            result = await session.execute(select(User).where(User.email == actual_email))
            user = result.scalar_one_or_none()
            if not user:
                user = User(
                    employee_code=f"MOCK-{role_name[:3].upper()}",
                    first_name="Mock",
                    last_name=role_name,
                    email=actual_email,
                    login_provider="GOOGLE",
                    status="Active"
                )
                user.roles.append(role)
                session.add(user)
            else:
                # Add role if missing
                if role not in user.roles:
                    user.roles.append(role)
            
            # If the user is CEO, also give them the Admin role
            if role_name == "CEO":
                admin_result = await session.execute(select(Role).where(Role.role_name == "Admin"))
                admin_role = admin_result.scalar_one_or_none()
                if admin_role and admin_role not in user.roles:
                    user.roles.append(admin_role)

        await session.commit()
        print("Mock users seeded.")

if __name__ == "__main__":
    asyncio.run(seed())
