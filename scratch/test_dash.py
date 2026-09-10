import asyncio
import httpx

async def main():
    async with httpx.AsyncClient(base_url="http://127.0.0.1:8000/api/v1") as client:
        resp = await client.post("/login", data={"username": "c.anisetty@dataeko.ai", "password": "Password123!"})
        if resp.status_code != 200:
            print("Login failed:", resp.text)
            return
        token = resp.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}
        
        for ep in ["dashboard", "dashboard/stats", "dashboard/pending-claims", "dashboard/recent-requisitions", "dashboard/recent-expenses", "dashboard/my-assets"]:
            r = await client.get(f"/{ep}", headers=headers)
            print(f"{ep}: {r.status_code}")
            if r.status_code != 200:
                print(r.text)

asyncio.run(main())
