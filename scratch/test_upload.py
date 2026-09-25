import asyncio
import httpx

async def main():
    async with httpx.AsyncClient() as client:
        # We need a token. We can get it from /api/v1/auth/login or similar?
        pass

if __name__ == "__main__":
    asyncio.run(main())
