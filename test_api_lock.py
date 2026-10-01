import asyncio
from httpx import AsyncClient, ASGITransport
from src.main import app

async def main():
    from src.auth.dependencies import PermissionChecker
    
    class DummyPermissionChecker:
        def __init__(self, required_permission):
            pass
        async def __call__(self, *args, **kwargs):
            from src.models.auth import User, Role
            role = Role(role_name="Admin")
            return User(user_id=1, email="test@dataeko.ai", status="Active", roles=[role])

    app.dependency_overrides[PermissionChecker] = DummyPermissionChecker
    
    # Wait, PermissionChecker is instantiated with an argument! It's a parameterized dependency.
    # FastAPI handles parameterized dependencies differently.
    # Let's just override `get_current_user` and skip PermissionChecker, wait, we can't skip it if it's explicitly Depends(PermissionChecker(...))
    pass

asyncio.run(main())
