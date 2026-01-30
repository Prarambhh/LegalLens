"""
Chat API Router
Provides the /api/chat endpoint for legal Q&A using RAG.
"""

from typing import Optional, List
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.services.rag_service import RAGService


router = APIRouter()


# ============================================================================
# Request/Response Models
# ============================================================================

class ChatMessage(BaseModel):
    """A single message in the chat."""
    role: str = Field(..., description="'user' or 'assistant'")
    content: str = Field(..., description="Message content")


class ChatRequest(BaseModel):
    """Request body for chat endpoint."""
    message: str = Field(..., min_length=3, max_length=2000, description="User's legal query")
    act_filter: Optional[str] = Field(None, description="Filter by act name (e.g., 'BNS', 'IPC')")
    top_k: int = Field(5, ge=1, le=10, description="Number of sections to retrieve")
    conversation_history: Optional[List[ChatMessage]] = Field(None, description="Previous messages for context")


class CitationResponse(BaseModel):
    """Citation information in response."""
    index: int
    act_name: str
    section_number: str
    title: Optional[str]
    content_snippet: str


class ChatResponse(BaseModel):
    """Response from chat endpoint."""
    answer: str
    citations: List[CitationResponse]
    query_intent: str
    is_relevant: bool


# ============================================================================
# Endpoints
# ============================================================================

@router.post("/", response_model=ChatResponse)
async def chat(
    request: ChatRequest,
    db: AsyncSession = Depends(get_db)
):
    """
    Legal Q&A endpoint using RAG pipeline.
    
    The pipeline:
    1. Checks if query is relevant to Indian law (guardrail)
    2. Classifies intent (research, comparison, drafting, definition)
    3. Performs hybrid search (semantic + keyword)
    4. Generates answer with citations using Gemini
    
    Example queries:
    - "What is the punishment for murder under BNS?"
    - "Compare IPC 420 with BNS equivalent"
    - "What are the bail provisions in BNSS?"
    """
    try:
        rag_service = RAGService(db)
        
        result = await rag_service.query(
            query=request.message,
            top_k=request.top_k,
            act_filter=request.act_filter
        )
        
        return ChatResponse(
            answer=result.answer,
            citations=[
                CitationResponse(
                    index=c.index,
                    act_name=c.act_name,
                    section_number=c.section_number,
                    title=c.title,
                    content_snippet=c.content_snippet
                )
                for c in result.citations
            ],
            query_intent=result.query_intent.value,
            is_relevant=result.is_relevant
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error processing chat request: {str(e)}"
        )


@router.get("/health")
async def chat_health():
    """Health check for chat service."""
    return {"status": "healthy", "service": "chat"}
