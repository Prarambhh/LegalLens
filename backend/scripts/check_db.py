import asyncio
import os
import sys

from sqlalchemy import text

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.database import get_engine


async def check_db_connection():
    print("Checking connection...")

    try:
        engine = get_engine()
        async with engine.connect() as conn:
            print("Database connection successful!")

            tables = ["acts", "sections", "mappings", "case_law"]
            for table_name in tables:
                try:
                    result = await conn.execute(text(f"SELECT COUNT(*) FROM {table_name}"))
                    count = result.scalar()
                    print(f"{table_name}: {count}")
                except Exception as e:
                    print(f"{table_name}: Error ({e})")

    except Exception as e:
        print(f"Database connection failed: {e}")


if __name__ == "__main__":
    asyncio.run(check_db_connection())
