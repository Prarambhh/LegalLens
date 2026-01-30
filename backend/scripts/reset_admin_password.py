
import asyncio
import sys
import os
from sqlalchemy import select
from app.database import get_session_factory
from app.models.user import User, UserRole
from app.core import security

sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

async def reset_admin_password():
    session_factory = get_session_factory()
    async with session_factory() as session:
        result = await session.execute(select(User).where(User.email == "admin@legallens.com"))
        user = result.scalars().first()
        
        new_hash = security.get_password_hash("password123")
        
        if user:
            print("Updating existing admin user password...")
            user.hashed_password = new_hash
            user.is_active = True
            user.role = UserRole.ADMIN
        else:
            print("Creating new admin user...")
            user = User(
                email="admin@legallens.com",
                hashed_password=new_hash,
                role=UserRole.ADMIN,
                is_active=True
            )
            session.add(user)
            
        await session.commit()
        print("✅ Admin user credentials reset to: admin@legallens.com / password123")

if __name__ == "__main__":
    asyncio.run(reset_admin_password())
