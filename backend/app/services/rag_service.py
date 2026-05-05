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
from langchain_core.output_parsers import StrOutputParser, JsonOutputParser
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
            model="llama-3.3-70b-versatile",
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
        system_instruction = self.SYSTEM_PROMPT
        user_prompt = query
        
        if intent == QueryIntent.COMPARISON:
            user_prompt = f"Compare the old and new law provisions for: {query}"
        elif intent == QueryIntent.DEFINITION:
            user_prompt = f"Define the following legal term: {query}"
        elif intent == QueryIntent.DRAFTING:
            user_prompt = f"Draft the following legal document: {query}"
            # Relaxed prompt for drafting to allow internal knowledge of formats
            system_instruction = """You are an expert Indian Legal Drafting Assistant.
Your task is to draft professional legal documents (Bail Applications, Affidavits, Vakalatnamas, etc.) for Indian Courts.
1. Use standard legal formats compliant with BNS, BNSS, and CPC.
2. Include clear placeholders like [CLIENT NAME], [DATE], [COURT NAME] in uppercase.
3. You may use your internal knowledge for the document structure/format.
4. If the provided Context contains relevant sections (e.g. Section 483 BNSS), cite them in the content.
5. Ensure the tone is formal and respectful (e.g., "Most Respectfully Showeth").

CONTEXT FROM LEGAL SECTIONS (Use if relevant):
{context}"""

        prompt = ChatPromptTemplate.from_messages([
            ("system", system_instruction),
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
        fetch_k = 40 
        try:
            results = await self.search_service.hybrid_search(
                query=query,
                top_k=fetch_k,
                act_filter=act_filter
            )
        except Exception as e:
            print(f"Hybrid search failed: {e}")
            results = []
        
        # Step 3b: Case Law Search (gracefully handle if table is empty or errors)
        try:
            case_laws = await self.search_service.search_case_laws(query, top_k=3)
            results.extend(case_laws)
        except Exception as e:
            print(f"Case law search failed (table may be empty): {e}")
            # Continue without case laws - not critical
        
        if not results:
            return RAGResponse(
                answer="I couldn't find any relevant legal sections for your query. Please try rephrasing or using more specific legal terminology.",
                citations=[],
                query_intent=intent,
                is_relevant=True
            )
            
        # Step 3c: Re-ranking
        # Rerank to get best 15 results for context
        try:
            reranked_results = await self.rerank_results(query, results, top_k=15)
        except Exception as e:
            print(f"Reranking failed, using original order: {e}")
            reranked_results = results[:15]
        
        # Step 4: Format context and generate answer
        context, citations = self._format_context(reranked_results)
        answer = await self.generate_answer(query, context, intent)
        
        return RAGResponse(
            answer=answer,
            citations=citations,
            query_intent=intent,
            is_relevant=True
        )

    async def compare_laws(self, query: str) -> dict:
        """
        Compare old vs new law provisions.
        Returns structured data for frontend comparison view.
        """
        # Step 1: Identify Target Sections using LLM
        identify_prompt = """You are an expert in Indian Law Transition (IPC -> BNS, CrPC -> BNSS, IEA -> BSA).
        Identify the corresponding section mapping using your internal legal knowledge.
        
        Query: {query}
        
        Examples:
        - IPC 302 (Murder) -> BNS 103
        - IPC 420 (Cheating) -> BNS 318
        - IPC 320 (Grievous Hurt) -> BNS 116 (or 117)
        - IPC 376 (Rape) -> BNS 64
        
        Respond with raw JSON only. Do not add markdown backticks.
        {{
            "old_act": "Act Name (IPC/CrPC/IEA)",
            "old_section": "Section Number",
            "new_act": "Act Name (BNS/BNSS/BSA)", 
            "new_section": "Section Number",
            "is_found": true
        }}
        """
        
        try:
            import json
            prompt = ChatPromptTemplate.from_template(identify_prompt)
            # Use StrOutputParser + Parse JSON manually to handle model chatter
            chain = prompt | self.classifier_llm | StrOutputParser()
            result_str = await chain.ainvoke({"query": query})
            
            # Extract JSON 
            result_str = result_str.strip()
            
            if "```json" in result_str:
                result_str = result_str.split("```json")[1].split("```")[0]
            elif "```" in result_str:
                result_str = result_str.split("```")[1].split("```")[0]
            elif "{" in result_str:
                start = result_str.find("{")
                end = result_str.rfind("}") + 1
                result_str = result_str[start:end]
                
            target = json.loads(result_str)
            
            if not target.get("is_found"):
                return None
                
            old_act_name = target['old_act']
            old_sec_num = target['old_section']
            new_act_name = target['new_act']
            new_sec_num = target['new_section']
            
            # Map short names to full names for better LLM context
            full_names = {
                "BNS": "Bharatiya Nyaya Sanhita 2023",
                "BNSS": "Bharatiya Nagarik Suraksha Sanhita 2023",
                "BSA": "Bharatiya Sakshya Adhiniyam 2023",
                "IPC": "Indian Penal Code 1860",
                "CrPC": "Code of Criminal Procedure 1973",
                "IEA": "Indian Evidence Act 1872"
            }
            new_act_full = full_names.get(new_act_name, new_act_name)
            old_act_full = full_names.get(old_act_name, old_act_name)
            
            # Step 2: Retrieve New Law Text from DB
            new_text = ""
            new_title = ""
            try:
                search_query = f"{new_act_name} Section {new_sec_num}"
                results = await self.search_service.hybrid_search(search_query, top_k=1, act_filter=new_act_name)
                
                if results and results[0].section_number == str(new_sec_num):
                    new_text = results[0].content
                    new_title = results[0].title or f"{new_act_name} {new_sec_num}"
            except Exception as e:
                print(f"DB lookup for new law failed: {e}")
            
            if not new_text:
                # Fallback: Ask LLM with specific context
                gen_prompt = f"""Provide the verbatim statutory text of Section {new_sec_num} of the {new_act_full}.
                Do not add introductory text. Just provide the section title and content.
                """
                new_text = await (ChatPromptTemplate.from_template(gen_prompt) | self.llm | StrOutputParser()).ainvoke({})
                new_title = f"{new_act_name} {new_sec_num}"

            # Step 3: Retrieve Old Law Text
            old_text_prompt = f"""Provide the verbatim statutory text and title of Section {old_sec_num} of the {old_act_full}.
            Do not add introductory text.
            """
            old_content_raw = await (ChatPromptTemplate.from_template(old_text_prompt) | self.llm | StrOutputParser()).ainvoke({})
            old_title = f"{old_act_name} {old_sec_num}"
            old_text = old_content_raw

            # Step 4: Generate Comparison Analysis
            analyze_prompt = """Compare these two legal sections:
            
            OLD LAW ({old_act} {old_sec}):
            {old_text}
            
            NEW LAW ({new_act} {new_sec}):
            {new_text}
            
            Generate a structured JSON comparison:
            {{
                "change_type": "modified", 
                "summary": "Brief summary of changes.",
                "diff": {{
                    "removed": ["Short phrases removed"],
                    "added": ["Short phrases added"]
                }}
            }}
            """
            
            analysis_chain = ChatPromptTemplate.from_template(analyze_prompt) | self.llm | StrOutputParser()
            analysis_str = await analysis_chain.ainvoke({
                "old_act": old_act_name, "old_sec": old_sec_num, "old_text": old_text,
                "new_act": new_act_name, "new_sec": new_sec_num, "new_text": new_text
            })
            
            # Extract JSON from analysis
            analysis_str = analysis_str.strip()
            if "```json" in analysis_str:
                analysis_str = analysis_str.split("```json")[1].split("```")[0]
            elif "```" in analysis_str:
                analysis_str = analysis_str.split("```")[1].split("```")[0]
            elif "{" in analysis_str:
                start = analysis_str.find("{")
                end = analysis_str.rfind("}") + 1
                analysis_str = analysis_str[start:end]
            
            try:
                analysis = json.loads(analysis_str)
            except:
                analysis = {} # Fallback to empty if parsing fails
            
            # Construct Response
            return {
                "old": {
                    "id": f"{old_act_name.lower()}_{old_sec_num}",
                    "act": old_act_name,
                    "section": old_sec_num,
                    "title": old_title,
                    "content": old_text
                },
                "new": {
                    "id": f"{new_act_name.lower()}_{new_sec_num}",
                    "act": new_act_name,
                    "section": new_sec_num,
                    "title": new_title,
                    "content": new_text
                },
                "mapping": {
                    "oldSectionId": f"{old_act_name.lower()}_{old_sec_num}",
                    "newSectionId": f"{new_act_name.lower()}_{new_sec_num}",
                    "changeType": analysis.get("change_type", "modified"),
                    "summary": analysis.get("summary", "Analysis unavailable"),
                    "diff": analysis.get("diff", {"added": [], "removed": []})
                }
            }
            
        except Exception as e:
            print(f"Comparison failed: {e}")
            import traceback
            traceback.print_exc()
            return None
