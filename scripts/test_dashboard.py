import asyncio
import httpx

async def main():
    async with httpx.AsyncClient() as client:
        # Login
        resp = await client.post('http://localhost:8080/api/v1/auth/login', json={'email': 'cfo@dataeko.ai', 'password': 'password123'})
        if resp.status_code != 200:
            print("Login failed:", resp.text)
            return
        token = resp.json()['access_token']
        print("Logged in successfully.")
        
        # Dashboard
        resp = await client.get('http://localhost:8080/api/v1/dashboard', headers={'Authorization': f'Bearer {token}'})
        print(f"Dashboard status: {resp.status_code}")
        print("Dashboard response:", resp.text)

asyncio.run(main())
