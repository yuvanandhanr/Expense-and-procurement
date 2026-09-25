import asyncio
from httpx import AsyncClient, ASGITransport
from src.main import app

async def test():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        # Assuming Rachel Foster's email. I will try the mock login endpoint.
        # Who is Rachel Foster? Let's query the DB for Rachel's email.
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
            print(f"Testing for {email}")
            
        response = await ac.post("/api/v1/auth/google", json={"credential": f"mock_google_{email}"})
        token = response.json().get("access_token")
        
        headers = {"Authorization": f"Bearer {token}"}
        
        res = await ac.get("/api/v1/dashboard", headers=headers)
        print(f"/api/v1/dashboard: {res.status_code}")
        if res.status_code == 500:
            print(res.text)

asyncio.run(test())
