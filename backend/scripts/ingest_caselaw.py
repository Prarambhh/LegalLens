import sys
import os
import json
import asyncio
from datetime import datetime

# Add the parent directory to sys.path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.database import get_db
from app.models.case_law import CaseLaw
from app.services.embedding_service import get_embedding_service
from sqlalchemy import text

async def ingest_caselaws():
    print("🚀 Starting Case Law ingestion...")
    
    # Initialize services
    embedding_service = get_embedding_service()
    
    # Load data
    data_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), "data", "sample_caselaws.json")
    print(f"📂 Reading data from: {data_path}")
    
    with open(data_path, 'r', encoding='utf-8') as f:
        cases = json.load(f)
    
    print(f"ℹ️ Found {len(cases)} cases to ingest.")
    
    async for session in get_db():
        try:
            # Check if table exists (basic check)
            await session.execute(text("SELECT 1"))
            print("✅ Database connection successful.")
            
            count = 0
            for case_data in cases:
                print(f"   Processing: {case_data['title']}")
                
                # Generate embedding
                # Combine title, content, and headnotes for rich embedding
                text_to_embed = f"{case_data['title']} {case_data['headnotes']} {case_data['content']}"
                embedding = embedding_service.embed(text_to_embed)
                
                # Create CaseLaw object
                case_law = CaseLaw(
                    title=case_data['title'],
                    citation=case_data.get('citation'),
                    case_number=case_data.get('case_number'),
                    court_name=case_data['court_name'],
                    judgment_date=datetime.strptime(case_data['judgment_date'], "%Y-%m-%d").date() if case_data.get('judgment_date') else None,
                    content=case_data['content'],
                    headnotes=case_data.get('headnotes'),
                    keywords=case_data.get('keywords'),
                    embedding=embedding
                )
                
                session.add(case_law)
                count += 1
            
            await session.commit()
            print(f"✅ Successfully ingested {count} case laws.")
            
        except Exception as e:
            await session.rollback()
            print(f"❌ Error during ingestion: {e}")
            raise e
        finally:
            # We don't need to close the session explicitly as the context manager handles it,
            # but since we are using 'async for' on a generator that yields, we just break.
            break

if __name__ == "__main__":
    asyncio.run(ingest_caselaws())
