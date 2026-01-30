"""
Document Service
Handles document parsing (PDF, DOCX) and AI analysis.
"""

import io
from typing import Optional, Dict, Any
import PyPDF2
from docx import Document
from fastapi import UploadFile, HTTPException
from langchain_groq import ChatGroq
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import JsonOutputParser

from app.config import get_settings

settings = get_settings()

class DocumentService:
    """Service for parsing and analyzing legal documents."""

    def __init__(self):
        # Use Groq Llama 3.3 for analysis
        self.llm = ChatGroq(
            model="llama-3.3-70b-versatile",
            api_key=settings.groq_api_key,
            temperature=0.2,
        )
        
        self.ANALYSIS_PROMPT = """You are an expert Legal AI Assistant. Analyze the following legal document text and provide a structured analysis in JSON format.
        
        Crucially, you must identify "anomalies" or suspicious clauses that might be risky, unfair, or legally unsound. For each anomaly, you MUST provide the EXACT quote from the text so it can be highlighted.

        Document Text:
        {text}
        
        Output JSON Structure:
        {{
            "summary": "Concise summary of the document (max 200 words)",
            "document_type": "Type of document (e.g., Contract, Court Order, Notice, Agreement)",
            "key_parties": ["List of names/parties involved"],
            "key_clauses": [
                {{
                    "title": "Clause Title (e.g., Termination, Indemnity)",
                    "content": "Brief explanation of the clause",
                    "risk_level": "Low/Medium/High"
                }}
            ],
            "anomalies": [
                {{
                    "quote": "Exact substring from the text that is suspicious (MUST MATCH EXACTLY)",
                    "issue": "Explanation of why this is suspicious or wrong",
                    "suggestion": "What should be written instead or how to fix it",
                    "severity": "High/Medium/Low"
                }}
            ],
            "risks": ["List of potential legal risks or liabilities"],
            "jurisdiction": "Applicable jurisdiction if mentioned",
            "dates": ["Important dates mentioned"]
        }}
        """

    async def parse_document(self, file: UploadFile) -> str:
        """Extract text from PDF or DOCX file."""
        content = await file.read()
        file_ext = file.filename.split('.')[-1].lower()
        
        text = ""
        
        try:
            if file_ext == 'pdf':
                pdf_reader = PyPDF2.PdfReader(io.BytesIO(content))
                for page in pdf_reader.pages:
                    text += page.extract_text() + "\n"
                    
            elif file_ext in ['docx', 'doc']:
                doc = Document(io.BytesIO(content))
                for para in doc.paragraphs:
                    text += para.text + "\n"
                    
            elif file_ext == 'txt':
                text = content.decode('utf-8')
                
            else:
                raise HTTPException(status_code=400, detail="Unsupported file format. Please upload PDF, DOCX, or TXT.")
                
            if not text.strip():
                raise HTTPException(status_code=400, detail="Could not extract text from document. It might be empty or scanned images.")
                
            return text
            
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Error parsing document: {str(e)}")
            
    async def analyze_document(self, text: str) -> Dict[str, Any]:
        """Analyze legal document text using LLM."""
        prompt = ChatPromptTemplate.from_template(self.ANALYSIS_PROMPT)
        chain = prompt | self.llm | JsonOutputParser()
        
        try:
            # Truncate text context limit
            truncated_text = text[:25000]
            
            result = await chain.ainvoke({"text": truncated_text})
            return result
            
        except Exception as e:
            print(f"Error analyzing document: {e}") 
            raise HTTPException(status_code=500, detail=f"Error analyzing document: {str(e)}")
