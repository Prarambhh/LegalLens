
import asyncio
from app.database import get_db
from sqlalchemy import text

async def check_duplicates():
    async for db in get_db():
        # Check BNSS (ID 26) Section 300
        print("--- BNSS (ID 26) Section 300 candidates ---")
        result = await db.execute(text(
            "SELECT id, section_number, title, length(content) "
            "FROM sections "
            "WHERE act_id = 26 AND section_number LIKE '300%'"
        ))
        rows = result.fetchall()
        for row in rows:
            print(row)
            
        # Check BNS (ID 35) Section 103
        print("\n--- BNS (ID 35) Section 103 candidates ---")
        result = await db.execute(text(
            "SELECT id, section_number, title, length(content) "
            "FROM sections "
            "WHERE act_id = 35 AND section_number = '103'"
        ))
        rows = result.fetchall()
        for row in rows:
            print(row)

if __name__ == "__main__":
    asyncio.run(check_duplicates())
