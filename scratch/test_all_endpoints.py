import asyncio
from httpx import AsyncClient, ASGITransport
from src.main import app

async def test():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        response = await ac.post("/api/v1/auth/google", json={"credential": "mock_google_y.raja@dataeko.ai"})
        token = response.json().get("access_token")
        
        headers = {"Authorization": f"Bearer {token}"}
        
        endpoints = [
            "/api/v1/approvals",
            "/api/v1/expenses",
            "/api/v1/dashboard",
            "/api/v1/purchase-requisitions",
            "/api/v1/asset-incidents"
        ]
        
        for ep in endpoints:
            res = await ac.get(ep, headers=headers)
            print(f"{ep}: {res.status_code}")
            if res.status_code == 500:
                print(res.text)

asyncio.run(test())
