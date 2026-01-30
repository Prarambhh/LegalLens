import sys
import os
import asyncio

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.database import get_db
from app.services.search_service import SearchService, SearchResult

async def test_caselaw_search():
    print("🔎 Testing Case Law Search...")
    
    async for session in get_db():
        service = SearchService(session)
        
        # Query about bail (should find the Maharashtra case)
        query = "bail in non-bailable offences"
        print(f"\nQuery: {query}")
        
        results = await service.search_case_laws(query, top_k=2)
        
        if results:
            for r in results:
                print(f"   - Found: {r.title} | Court: {r.act_name} | Score: {r.similarity_score:.4f}")
            print("✅ Case Law Search works!")
        else:
            print("❌ No case laws found.")
            
        break

if __name__ == "__main__":
    asyncio.run(test_caselaw_search())
