import asyncio
import asyncpg

async def main():
    try:
        conn = await asyncpg.connect('postgresql://app_user.qagextokkrxrrmowyser:AppSecurePassword123!@aws-0-ap-south-1.pooler.supabase.com:6543/postgres')
        print("Connected!")
        res = await conn.fetch("SELECT 1")
        print(res)
        await conn.close()
    except Exception as e:
        print(f"Failed: {e}")

asyncio.run(main())
