"""
Embedding Service
Generates text embeddings using HuggingFace sentence-transformers.
"""

from functools import lru_cache
from typing import List
from sentence_transformers import SentenceTransformer

from app.config import get_settings

settings = get_settings()


class EmbeddingService:
    """
    Generates embeddings using HuggingFace sentence-transformers.
    Uses paraphrase-multilingual-MiniLM-L12-v2 for English/Hindi support.
    """
    
    _instance = None
    _model = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    def __init__(self):
        if EmbeddingService._model is None:
            print(f"📦 Loading embedding model: {settings.embedding_model}")
            EmbeddingService._model = SentenceTransformer(settings.embedding_model)
            print(f"✅ Model loaded. Dimension: {self.dimension}")
    
    @property
    def model(self) -> SentenceTransformer:
        return EmbeddingService._model
    
    @property
    def dimension(self) -> int:
        return self.model.get_sentence_embedding_dimension()
    
    def embed(self, text: str) -> List[float]:
        """Generate embedding for a single text."""
        embedding = self.model.encode(text, convert_to_numpy=True)
        return embedding.tolist()
    
    def embed_batch(self, texts: List[str], batch_size: int = 32) -> List[List[float]]:
        """Generate embeddings for multiple texts."""
        embeddings = self.model.encode(
            texts,
            batch_size=batch_size,
            show_progress_bar=False,
            convert_to_numpy=True
        )
        return [emb.tolist() for emb in embeddings]


@lru_cache()
def get_embedding_service() -> EmbeddingService:
    """Get singleton embedding service instance."""
    return EmbeddingService()
