
import asyncio
import sys
import os
from sqlalchemy import text
from app.database import get_session_factory

sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

async def delete_recent_acts():
    session_factory = get_session_factory()
    async with session_factory() as session:
        # Delete acts > 7 (The ones we just uploaded with bad parsing)
        # Using raw SQL to avoid cascade issues if models aren't set up for it, 
        # though assuming CASCADE constraint exists on sections.
        print("Deleting Acts with ID >= 8...")
        
        # Delete Sections first (just in case no cascade)
        await session.execute(text("DELETE FROM sections WHERE act_id >= 8"))
        
        # Delete Acts
        result = await session.execute(text("DELETE FROM acts WHERE id >= 8"))
        await session.commit()
        print(f"✅ Deleted {result.rowcount} Acts.")

if __name__ == "__main__":
    asyncio.run(delete_recent_acts())
