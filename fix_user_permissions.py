import asyncio
from sqlalchemy import select
from src.database.dependency import get_db_session
from src.models.auth import Role, Permission

async def main():
    async for db in get_db_session():
        try:
            # 1. Ensure `users.view` permission exists
            result = await db.execute(select(Permission).where(Permission.permission_name == "users.view"))
            users_view_perm = result.scalar_one_or_none()
            
            if not users_view_perm:
                print("Permission 'users.view' not found. Creating it.")
                users_view_perm = Permission(permission_name="users.view", description="View users")
                db.add(users_view_perm)
                await db.flush()
                
            # 2. Get CFO, CEO, Finance Manager roles
            roles_to_update = ["CFO", "CEO", "Finance Manager", "Manager"]
            result = await db.execute(select(Role).where(Role.role_name.in_(roles_to_update)))
            roles = result.scalars().all()
            
            for role in roles:
                # Check if it already has the permission
                has_perm = any(p.permission_name == "users.view" for p in role.permissions)
                if not has_perm:
                    print(f"Adding users.view to {role.role_name}")
                    role.permissions.append(users_view_perm)
                else:
                    print(f"{role.role_name} already has users.view")
                    
            await db.commit()
            print("Successfully updated role permissions!")
            
        except Exception as e:
            print("Error:", repr(e))
            import traceback
            traceback.print_exc()
        break

asyncio.run(main())
