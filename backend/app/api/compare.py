from fastapi import APIRouter, Depends, HTTPException
from typing import Dict, Any, Optional
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession
from app.database import get_db
from app.services.rag_service import RAGService

router = APIRouter()

class CompareRequest(BaseModel):
    query: str

@router.post("/analyze")
async def analyze_comparison(
    request: CompareRequest,
    db: AsyncSession = Depends(get_db)
):
    """
    Compare old vs new law (IPC vs BNS) for a given query (e.g. 'IPC 302').
    """
    try:
        rag = RAGService(db)
        result = await rag.compare_laws(request.query)
        if not result:
            raise HTTPException(status_code=404, detail="Could not identify or find relevant sections to compare.")
        return result
    except HTTPException:
        raise
    except Exception as e:
        import traceback
        print(f"Comparison endpoint error: {e}")
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Comparison error: {str(e)}")
