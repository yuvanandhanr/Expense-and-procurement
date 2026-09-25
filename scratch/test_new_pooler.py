import asyncio
import asyncpg

async def main():
    # URL encode the % in the password: postgres%123 -> postgres%25123
    url = 'postgresql://postgres.qagextokkrxrrmowyser:postgres%25123@aws-1-ap-south-1.pooler.supabase.com:5432/postgres'
    try:
        conn = await asyncpg.connect(url, timeout=10)
        res = await conn.fetch("SELECT current_user, current_database()")
        print(f"Connected! User: {res[0]['current_user']}, DB: {res[0]['current_database']}")
        
        # Test a real table query
        count = await conn.fetch("SELECT count(*) as cnt FROM users")
        print(f"Users table has {count[0]['cnt']} rows")
        
        await conn.close()
        print("SUCCESS - Pooler connection works!")
    except Exception as e:
        print(f"FAILED: {type(e).__name__}: {e}")

asyncio.run(main())
