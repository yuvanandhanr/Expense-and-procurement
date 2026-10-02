import asyncio
from httpx import AsyncClient, ASGITransport
from src.main import app

async def main():
    from src.auth.dependencies import PermissionChecker, get_current_user
    from src.models.auth import User, Role, Permission
    
    # We must patch PermissionChecker directly since it's a callable class dependency.
    # We can just return a dummy user in get_current_user.
    # But wait, PermissionChecker uses get_current_user. If the user HAS the role, it passes.
    
    async def override_get_current_user():
        perm = Permission(permission_name="admin.settings")
        perm2 = Permission(permission_name="users.view")
        role = Role(role_name="Admin", permissions=[perm, perm2])
        user = User(user_id=1, email="test@dataeko.ai", status="Active", roles=[role])
        return user
        
    app.dependency_overrides[get_current_user] = override_get_current_user
    
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://testserver") as client:
        res = await client.get("/api/v1/users")
        print("Get users status:", res.status_code)
        if res.status_code == 200:
            users = res.json()
            if users:
                user_id = users[0]["user_id"]
                lock_res = await client.post(f"/api/v1/users/{user_id}/lock")
                print(f"Lock status: {lock_res.status_code}, body: {lock_res.text}")
            else:
                print("No users in db")
        else:
            print("Error getting users:", res.text)

asyncio.run(main())
