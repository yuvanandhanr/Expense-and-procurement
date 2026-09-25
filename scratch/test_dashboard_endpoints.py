import asyncio
from httpx import AsyncClient, ASGITransport
from src.main import app

async def test():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        # Assuming Rachel Foster's email
        from src.database.session import async_session
        from src.models.auth import User
        from sqlalchemy import select
        
        async with async_session() as db:
            res = await db.execute(select(User).where(User.first_name == "Rachel", User.last_name == "Foster"))
            rachel = res.scalar_one_or_none()
            if not rachel:
                print("Rachel not found")
                return
            email = rachel.email
            
        response = await ac.post("/api/v1/auth/google", json={"credential": f"mock_google_{email}"})
        token = response.json().get("access_token")
        
        headers = {"Authorization": f"Bearer {token}"}
        
        endpoints = [
            "/api/v1/dashboard",
            "/api/v1/expenses",
            "/api/v1/pr",
            "/api/v1/approvals",
            "/api/v1/assets/my-assets"
        ]
        
        for ep in endpoints:
            res = await ac.get(ep, headers=headers)
            print(f"{ep}: {res.status_code}")
            if res.status_code == 500:
                print(res.text)

asyncio.run(test())
