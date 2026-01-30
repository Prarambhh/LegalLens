"""
Create Admin User Script
"""
import sys
import os
import asyncio
from sqlalchemy import select

# Add backend directory to path
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from app.database import get_session_factory, init_db
from app.models.user import User, UserRole
from app.core.security import get_password_hash

async def create_admin(email, password):
    await init_db()
    session_factory = get_session_factory()
    async with session_factory() as session:
        result = await session.execute(select(User).where(User.email == email))
        user = result.scalars().first()
        
        if user:
            print(f"User {email} already exists. Updating password...")
            user.hashed_password = get_password_hash(password)
            await session.commit()
            print(f"Password updated for {email}.")
            return

        new_user = User(
            email=email,
            hashed_password=get_password_hash(password),
            role=UserRole.ADMIN,
            is_active=True
        )
        session.add(new_user)
        await session.commit()
        print(f"Admin user {email} created successfully.")

if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("Usage: python create_admin.py <email> <password>")
        sys.exit(1)
        
    email = sys.argv[1]
    password = sys.argv[2]
    
    asyncio.run(create_admin(email, password))
