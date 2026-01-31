from fastapi import APIRouter, UploadFile, File, HTTPException, Depends
from typing import Dict, Any, List, Optional
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser

from app.services.document_service import DocumentService
from app.services.search_service import SearchService
from app.database import get_db

router = APIRouter()
document_service = DocumentService()

# --- Models ---
class DocumentChatRequest(BaseModel):
    query: str
    document_text: str

class CaseLawCitation(BaseModel):
    title: str
    snippet: str
    similarity: float

class DocumentChatResponse(BaseModel):
    answer: str
    citations: List[CaseLawCitation]

# --- Endpoints ---

@router.post("/analyze")
async def analyze_document(file: UploadFile = File(...)) -> Dict[str, Any]:
    """
    Analyze a legal document (PDF, DOCX, TXT) using Gemini.
    Returns structured analysis including summary, risks, key clauses, etc.
    """
    try:
        # 1. Parse Document
        text = await document_service.parse_document(file)
        
        # 2. Analyze
        analysis = await document_service.analyze_document(text)
        
        # 3. Enhance response with full text (for frontend highlighting)
        analysis["full_text"] = text
        
        return analysis
        
    except HTTPException as he:
        raise he
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/chat", response_model=DocumentChatResponse)
async def chat_with_document(
    request: DocumentChatRequest,
    db: AsyncSession = Depends(get_db)
):
    """
    Chat with a document, supplemented by external Case Law search.
    """
    try:
        # 2. Generate Answer using LLM
        prompt_template = """You are an expert Legal AI Assistant. Answer the user's question based ONLY on the provided Document Text.

        uploaded_document_text:
        {doc_text}

        user_query:
        {query}

        Answer:
        """
        
        prompt = ChatPromptTemplate.from_template(prompt_template)
        # Use the same LLM from document_service
        llm = document_service.llm 
        chain = prompt | llm | StrOutputParser()
        
        answer = await chain.ainvoke({
            "doc_text": request.document_text[:50000], # Context limit safety
            "query": request.query
        })

        return DocumentChatResponse(
            answer=answer,
            citations=[]
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
