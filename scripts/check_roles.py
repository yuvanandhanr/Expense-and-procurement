import asyncio
from src.database.session import async_session
from sqlalchemy import text

async def check_roles():
    async with async_session() as db:
        res = await db.execute(text("""
            SELECT u.email, r.role_name, r.status
            FROM users u 
            JOIN user_roles ur ON u.user_id = ur.user_id 
            JOIN roles r ON ur.role_id = r.role_id 
            WHERE u.email IN ('ceo@dataeko.ai', 'cfo@dataeko.ai');
        """))
        for row in res.fetchall():
            print(row.email, row.role_name, "Status:", row.status)

asyncio.run(check_roles())
