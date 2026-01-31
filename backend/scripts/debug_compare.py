import asyncio
import sys
import os

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app.database import get_session_factory
from app.services.rag_service import RAGService

async def test_compare():
    session_factory = get_session_factory()
    async with session_factory() as session:
        rag = RAGService(session)
        print("Comparing IPC 320...")
        try:
            result = await rag.compare_laws("IPC 378")
            print("Result:", result)
        except Exception as e:
            import traceback
            traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_compare())
