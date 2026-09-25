import asyncio
from httpx import AsyncClient, ASGITransport
from src.main import app

async def test():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        response = await ac.post("/api/v1/auth/google", json={"credential": "mock_google_y.raja@dataeko.ai"})
        token = response.json().get("access_token")
        print("Got token")
        
        response = await ac.get("/api/v1/approvals", headers={"Authorization": f"Bearer {token}"})
        print(response.status_code)
        if response.status_code != 200:
            print(response.text)
        else:
            print("OK")

asyncio.run(test())
