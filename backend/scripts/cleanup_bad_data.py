
import asyncio
import sys
import os
from sqlalchemy import text
from app.database import get_session_factory

sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

async def cleanup():
    session_factory = get_session_factory()
    async with session_factory() as session:
        print("Force deleting Acts 2-7...")
        
        # Delete sections for these acts
        await session.execute(text("DELETE FROM sections WHERE act_id IN (2, 3, 4, 5, 6, 7)"))
        
        # Delete the acts themselves
        await session.execute(text("DELETE FROM acts WHERE id IN (2, 3, 4, 5, 6, 7)"))
        
        await session.commit()
        print("✅ Force wipe complete.")

if __name__ == "__main__":
    asyncio.run(cleanup())
