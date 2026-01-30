
import asyncio
import sys
import os
from sqlalchemy import select
from app.database import get_session_factory
from app.models.user import User, UserRole
from app.core import security

sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

async def ensure_admin():
    session_factory = get_session_factory()
    async with session_factory() as session:
        result = await session.execute(select(User).where(User.email == "admin@legallens.com"))
        user = result.scalars().first()
        
        if not user:
            print("Creating admin user...")
            new_user = User(
                email="admin@legallens.com",
                hashed_password=security.get_password_hash("password123"), # Default password
                role=UserRole.ADMIN,
                is_active=True
            )
            session.add(new_user)
            await session.commit()
            print("✅ Admin user created: admin@legallens.com / password123")
        else:
            print("✅ Admin user already exists.")

if __name__ == "__main__":
    asyncio.run(ensure_admin())
