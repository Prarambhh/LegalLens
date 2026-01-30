import sys
import os
import asyncio
from unittest.mock import MagicMock

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.services.document_service import DocumentService

async def test_analysis():
    print("🧪 Testing Document Analysis Service...")
    
    service = DocumentService()
    
    # Sample legal text (Lease Agreement snippet)
    sample_text = """
    LEASE AGREEMENT
    
    This Lease Agreement (the "Agreement") is entered into on January 20, 2024, by and between:
    Landlord: John Doe, residing at 123 Main St.
    Tenant: Jane Smith, residing at 456 Elm St.
    
    1. TERM: The lease shall obtain for a period of 12 months, commencing on Feb 1, 2024.
    2. RENT: The Tenant agrees to pay Rs. 20,000 per month.
    3. TERMINATION: Either party may terminate this agreement with 30 days written notice.
    4. INDEMNITY: Tenant shall indemnify Landlord against any losses.
    """
    
    print(f"\n📄 Analyzing text ({len(sample_text)} chars)...")
    
    try:
        result = await service.analyze_document(sample_text)
        print("\n✅ Analysis Result:")
        import json
        print(json.dumps(result, indent=2))
        
        # Basic assertions
        if "summary" in result and "key_clauses" in result:
             print("\n✅ Structure validation passed.")
        else:
             print("\n❌ Structure validation failed.")
             
    except Exception as e:
        print(f"\n❌ Error: {e}")

if __name__ == "__main__":
    asyncio.run(test_analysis())
