import asyncio
import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.database import get_session_factory
from app.services.search_service import SearchService

async def test_search():
    print("Initializing DB...")
    session_factory = get_session_factory()
    async with session_factory() as session:
        print("Initializing SearchService...")
        search_service = SearchService(session)
        
        query = "theft"
        print(f"Searching for: {query}")
        
        try:
            results = await search_service.search_case_laws(query, top_k=3)
            print(f"Found {len(results)} results.")
            for r in results:
                print(f" - {r.title} ({r.similarity_score})")
        except Exception as e:
            print(f"Error: {e}")
            import traceback
            traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_search())
