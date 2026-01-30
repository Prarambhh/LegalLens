"""
RAG Service
Retrieval-Augmented Generation for legal Q&A using LangChain and Gemini.
"""

import re
from typing import List, Optional, Tuple
from dataclasses import dataclass
from enum import Enum

from langchain_groq import ChatGroq
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import get_settings
from app.services.search_service import SearchService, SearchResult

settings = get_settings()


class QueryIntent(str, Enum):
    """Classification of user query intent."""
    RESEARCH = "research"        # General legal research
    COMPARISON = "comparison"    # Compare old vs new law
    DRAFTING = "drafting"        # Help draft legal documents
    DEFINITION = "definition"    # Define legal terms
    IRRELEVANT = "irrelevant"    # Not related to Indian law


@dataclass
class Citation:
    """Represents a source citation."""
    index: int
    act_name: str
    section_number: str
    title: Optional[str]
    content_snippet: str
    
    def to_dict(self) -> dict:
        return {
            "index": self.index,
            "act_name": self.act_name,
            "section_number": self.section_number,
            "title": self.title,
            "content_snippet": self.content_snippet[:500]
        }


@dataclass
class RAGResponse:
    """Response from RAG pipeline."""
    answer: str
    citations: List[Citation]
    query_intent: QueryIntent
    is_relevant: bool
    
    def to_dict(self) -> dict:
        return {
            "answer": self.answer,
            "citations": [c.to_dict() for c in self.citations],
            "query_intent": self.query_intent.value,
            "is_relevant": self.is_relevant
        }


class RAGService:
    """
    Retrieval-Augmented Generation service for legal Q&A.
    
    Pipeline:
    1. Input Guardrails - Check if query is relevant to Indian law
    2. Query Router - Classify intent (research, comparison, drafting)
    3. Hybrid Search - Retrieve relevant sections
    4. LLM Generation - Generate answer with citations
    """
    
    # System prompt for legal assistant
    SYSTEM_PROMPT = """You are an expert Indian Legal Assistant specializing in criminal law. 
You help lawyers and citizens understand the transition from old laws (IPC, CrPC, IEA) to new Sanhitas (BNS, BNSS, BSA).

RULES:
1. Answer ONLY based on the provided context from legal sections
2. If the answer is not in the context, say "I don't have enough information to answer this question based on the available legal sections."
3. ALWAYS cite the source using format [1], [2], etc. matching the section numbers
4. Be precise and use legal terminology appropriately
5. For comparisons, clearly state what changed between old and new law
6. Keep answers concise but comprehensive

CONTEXT FROM LEGAL SECTIONS:
{context}

Remember: You are providing legal information, not legal advice. Always recommend consulting a qualified lawyer for specific cases."""

    GUARDRAIL_PROMPT = """Determine if the following query is related to Indian law (criminal law, IPC, BNS, CrPC, BNSS, legal procedures, court matters, FIR, charges, bail, etc.).

Query: {query}

Respond with ONLY 'relevant' or 'irrelevant'. Nothing else."""

    ROUTER_PROMPT = """Classify the intent of this legal query into ONE of these categories:
- research: General legal research or understanding provisions
- comparison: Comparing old law (IPC/CrPC/IEA) with new law (BNS/BNSS/BSA)
- drafting: Help with drafting legal documents, complaints, applications
- definition: Asking for definition of legal terms

Query: {query}

Respond with ONLY the category name. Nothing else."""

    def __init__(self, session: AsyncSession):
        self.session = session
        self.search_service = SearchService(session)
        
        # Initialize Groq LLM (High Performance)
        self.llm = ChatGroq(
            model="llama-3.3-70b-versatile",
            api_key=settings.groq_api_key,
            temperature=0.1
        )
        
        # Lighter model for classification tasks
        self.classifier_llm = ChatGroq(
            model="llama-3.1-8b-instant",
            api_key=settings.groq_api_key,
            temperature=0
        )
    
    async def check_relevance(self, query: str) -> bool:
        """Check if query is relevant to Indian law (input guardrail)."""
        prompt = ChatPromptTemplate.from_template(self.GUARDRAIL_PROMPT)
        chain = prompt | self.classifier_llm | StrOutputParser()
        
        try:
            result = await chain.ainvoke({"query": query})
            return result.strip().lower() == "relevant"
        except Exception as e:
            print(f"Guardrail check failed: {e}")
            return True  # Default to relevant on error
    
    async def classify_intent(self, query: str) -> QueryIntent:
        """Classify the intent of the query (query router)."""
        prompt = ChatPromptTemplate.from_template(self.ROUTER_PROMPT)
        chain = prompt | self.classifier_llm | StrOutputParser()
        
        try:
            result = await chain.ainvoke({"query": query})
            intent_str = result.strip().lower()
            
            intent_map = {
                "research": QueryIntent.RESEARCH,
                "comparison": QueryIntent.COMPARISON,
                "drafting": QueryIntent.DRAFTING,
                "definition": QueryIntent.DEFINITION
            }
            return intent_map.get(intent_str, QueryIntent.RESEARCH)
        except Exception as e:
            print(f"Intent classification failed: {e}")
            return QueryIntent.RESEARCH
    
    def _format_context(self, results: List[SearchResult]) -> Tuple[str, List[Citation]]:
        """Format search results as context for LLM and extract citations."""
        context_parts = []
        citations = []
        
        MAX_SECTION_CHARS = 2500
        MAX_TOTAL_CHARS = 20000
        current_chars = 0
        
        for i, result in enumerate(results, 1):
            if current_chars >= MAX_TOTAL_CHARS:
                break
                
            # Truncate content if too long
            content = result.content
            if len(content) > MAX_SECTION_CHARS:
                content = content[:MAX_SECTION_CHARS] + "... (truncated)"
            
            # Format section for context
            section_text = f"""
[{i}] {result.act_name} - Section {result.section_number}
Title: {result.title or 'N/A'}
Content: {content}
"""
            # Check if adding this section exceeds total limit
            if current_chars + len(section_text) > MAX_TOTAL_CHARS:
                # Add one last truncated version or just stop
                break
                
            context_parts.append(section_text)
            current_chars += len(section_text)
            
            # Create citation
            citations.append(Citation(
                index=i,
                act_name=result.act_name,
                section_number=result.section_number,
                title=result.title,
                content_snippet=result.content  # Keep full content for citation metadata if needed
            ))
        
        return "\n---\n".join(context_parts), citations
    
    async def generate_answer(
        self,
        query: str,
        context: str,
        intent: QueryIntent
    ) -> str:
        """Generate answer using LLM with context."""
        # Customize prompt based on intent
        user_prompt = query
        if intent == QueryIntent.COMPARISON:
            user_prompt = f"Compare the old and new law provisions for: {query}"
        elif intent == QueryIntent.DEFINITION:
            user_prompt = f"Define the following legal term: {query}"
        elif intent == QueryIntent.DRAFTING:
            user_prompt = f"Help draft or guide regarding: {query}"
        
        prompt = ChatPromptTemplate.from_messages([
            ("system", self.SYSTEM_PROMPT),
            ("human", "{query}")
        ])
        
        chain = prompt | self.llm | StrOutputParser()
        
        try:
            result = await chain.ainvoke({
                "context": context,
                "query": user_prompt
            })
            return result
        except Exception as e:
            return f"I apologize, but I encountered an error generating a response: {str(e)}"
    
    async def rerank_results(
        self,
        query: str,
        results: List[SearchResult],
        top_k: int = 5
    ) -> List[SearchResult]:
        """Rerank results using LLM scoring."""
        if not results:
            return []
            
        # If few results, just return them
        if len(results) <= top_k:
            return results
            
        # Format for ranking
        candidates = []
        for i, r in enumerate(results):
            candidates.append(f"ID: {i}\nContent: {r.act_name} {r.section_number}: {r.content[:300]}...")
            
        candidates_str = "\n---\n".join(candidates)
        
        RERANK_PROMPT = """Rate the relevance of the following legal sections to the query: "{query}"
        
        candidates:
        {candidates}
        
        Respond with a JSON object mapping ID to a relevance score (0-10).
        Example: {{"0": 9, "1": 3, "2": 0}}
        ONLY return the JSON."""
        
        prompt = ChatPromptTemplate.from_template(RERANK_PROMPT)
        chain = prompt | self.classifier_llm | StrOutputParser()
        
        try:
            import json
            response = await chain.ainvoke({
                "query": query,
                "candidates": candidates_str
            })
            
            # Extract JSON
            json_str = response.strip()
            if "```json" in json_str:
                json_str = json_str.split("```json")[1].split("```")[0]
            elif "{" not in json_str:
                return results[:top_k] # Fallback
                
            scores = json.loads(json_str)
            
            # Sort by score
            results.sort(key=lambda x: scores.get(str(results.index(x)), 0), reverse=True)
            
            return results[:top_k]
            
        except Exception as e:
            print(f"Reranking failed: {e}")
            return results[:top_k] # Fallback to original order

    async def query(
        self,
        query: str,
        top_k: int = 15,
        act_filter: Optional[str] = None
    ) -> RAGResponse:
        """
        Main RAG pipeline entry point.
        """
        # Step 1: Input Guardrails
        is_relevant = await self.check_relevance(query)
        
        if not is_relevant:
            return RAGResponse(
                answer="I'm sorry, but your query doesn't appear to be related to Indian law...",
                citations=[],
                query_intent=QueryIntent.IRRELEVANT,
                is_relevant=False
            )
        
        # Step 2: Query Router
        intent = await self.classify_intent(query)
        
        # Step 3: Hybrid Search (Match more candidates for reranking)
        fetch_k = 25 
        results = await self.search_service.hybrid_search(
            query=query,
            top_k=fetch_k,
            act_filter=act_filter
        )
        
        # Step 3b: Case Law Search
        case_laws = await self.search_service.search_case_laws(query, top_k=3)
        results.extend(case_laws)
        
        if not results:
            return RAGResponse(
                answer="I couldn't find any relevant legal sections...",
                citations=[],
                query_intent=intent,
                is_relevant=True
            )
            
        # Step 3c: Re-ranking
        # Rerank to get best 7 results for context
        reranked_results = await self.rerank_results(query, results, top_k=7)
        
        # Step 4: Format context and generate answer
        context, citations = self._format_context(reranked_results)
        answer = await self.generate_answer(query, context, intent)
        
        return RAGResponse(
            answer=answer,
            citations=citations,
            query_intent=intent,
            is_relevant=True
        )
