import sys
import os

# Add the parent directory to sys.path so we can import app modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.services.embedding_service import EmbeddingService
from app.config import get_settings

def test_multilingual_similarity():
    settings = get_settings()
    print(f"Testing model: {settings.embedding_model}")
    
    service = EmbeddingService()
    
    # English and Hindi equivalent sentences
    english_text = "Legal action against theft"
    hindi_text = "चोरी के खिलाफ कानूनी कार्रवाई"
    irrelevant_text = "How to bake a cake"
    
    print(f"\nText 1 (English): {english_text}")
    print(f"Text 2 (Hindi): {hindi_text}")
    print(f"Text 3 (Irrelevant): {irrelevant_text}")
    
    emb_en = service.embed(english_text)
    emb_hi = service.embed(hindi_text)
    emb_irr = service.embed(irrelevant_text)
    
    # Calculate cosine similarity manually or use service if available
    # Since service uses sentence_transformers, we can use util if imported, 
    # but let's just do a basic dot product for normalized vectors or use the service logic if exposed.
    # The service returns lists, so we can convert back to numpy or use scipy.
    
    from sentence_transformers import util
    import torch
    
    # Convert lists back to tensors for util.cos_sim
    tensor_en = torch.tensor([emb_en])
    tensor_hi = torch.tensor([emb_hi])
    tensor_irr = torch.tensor([emb_irr])
    
    sim_en_hi = util.cos_sim(tensor_en, tensor_hi).item()
    sim_en_irr = util.cos_sim(tensor_en, tensor_irr).item()
    
    print(f"\nSimilarity (English <-> Hindi): {sim_en_hi:.4f}")
    print(f"Similarity (English <-> Irrelevant): {sim_en_irr:.4f}")
    
    if sim_en_hi > 0.6:
        print("\n✅ PASS: High similarity between English and Hindi translation.")
    else:
        print("\n❌ FAIL: Low similarity between English and Hindi translation.")

    if sim_en_hi > sim_en_irr:
        print("✅ PASS: Translation is more similar than irrelevant text.")
    else:
        print("❌ FAIL: Irrelevant text is more similar.")

if __name__ == "__main__":
    test_multilingual_similarity()
