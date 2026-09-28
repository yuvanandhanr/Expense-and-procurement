import asyncio
from src.database.session import async_session
from sqlalchemy import text
import sys
import os

# Ensure the correct path is in sys.path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

async def main():
    async with async_session() as session:
        # Keep only these emails
        emails_to_keep = [
            'admin@dataeko.ai',
            'ceo@dataeko.ai',
            'cfo@dataeko.ai',
            'finance@dataeko.ai',
            'manager@dataeko.ai',
            'employee@dataeko.ai'
        ]
        
        # We may need to delete foreign key referencing rows first, like in refresh_tokens, user_roles
        
        try:
            # First, check what tables reference users
            # The models usually are: RefreshToken, UserRole
            
            delete_tokens = text("""
                DELETE FROM refresh_tokens 
                WHERE user_id IN (
                    SELECT id FROM users 
                    WHERE email NOT IN ('admin@dataeko.ai', 'ceo@dataeko.ai', 'cfo@dataeko.ai', 'finance@dataeko.ai', 'manager@dataeko.ai', 'employee@dataeko.ai')
                )
            """)
            await session.execute(delete_tokens)
            print("Deleted refresh_tokens")

            delete_user_roles = text("""
                DELETE FROM user_roles 
                WHERE user_id IN (
                    SELECT id FROM users 
                    WHERE email NOT IN ('admin@dataeko.ai', 'ceo@dataeko.ai', 'cfo@dataeko.ai', 'finance@dataeko.ai', 'manager@dataeko.ai', 'employee@dataeko.ai')
                )
            """)
            await session.execute(delete_user_roles)
            print("Deleted user_roles")

            delete_users = text("""
                DELETE FROM users 
                WHERE email NOT IN ('admin@dataeko.ai', 'ceo@dataeko.ai', 'cfo@dataeko.ai', 'finance@dataeko.ai', 'manager@dataeko.ai', 'employee@dataeko.ai')
            """)
            result = await session.execute(delete_users)
            print(f"Deleted {result.rowcount} users")

            await session.commit()
            print("Commit successful")

        except Exception as e:
            print("Error deleting users:", e)
            await session.rollback()

if __name__ == "__main__":
    asyncio.run(main())
