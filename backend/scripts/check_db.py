import sys
import os
import asyncio

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy import text
from app.config import get_settings

async def check_db_connection():
    settings = get_settings()
    print(f"Checking connection to: {settings.database_url.split('@')[-1]}") # Hide password
    
    try:
        engine = create_async_engine(settings.database_url)
        print("Engine created.")
        
        async with engine.connect() as conn:
            print("Connecting...")
            result = await conn.execute(text("SELECT 1"))
            print(f"Result: {result.scalar()}")
            print("✅ Database connection successful!")
            
    except Exception as e:
        print(f"❌ Database connection failed: {e}")

if __name__ == "__main__":
    asyncio.run(check_db_connection())
