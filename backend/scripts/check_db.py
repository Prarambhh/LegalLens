import sys
import os
import asyncio

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy import text
from app.database import get_engine

async def check_db_connection():
    print(f"Checking connection...")
    
    try:
        engine = get_engine()
        async with engine.connect() as conn:
            print("✅ Database connection successful!")
            
            # Check Counts
            tables = ["acts", "sections", "mappings", "case_law"]
            for t_name in tables:
                try:
                    result = await conn.execute(text(f"SELECT COUNT(*) FROM {t_name}"))
                    count = result.scalar()
                    print(f"📊 {t_name}: {count}")
                except Exception as e:
                    print(f"⚠️ {t_name}: Error ({e})")
            
    except Exception as e:
        print(f"❌ Database connection failed: {e}")

if __name__ == "__main__":
    asyncio.run(check_db_connection())
