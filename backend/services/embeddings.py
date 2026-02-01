"""Embedding generation service using VertexAI."""
import os
from typing import List, Optional
from google.cloud import aiplatform
import logging

logger = logging.getLogger(__name__)


class EmbeddingService:
    """Service for generating text embeddings using VertexAI."""
    
    def __init__(self):
        self.project_id = os.getenv("GOOGLE_CLOUD_PROJECT")
        self.location = os.getenv("VERTEX_AI_LOCATION", "us-central1")
        self.model_name = "text-embedding-004"
        self.dimensions = 768
        self._initialized = False
    
    def initialize(self):
        """Initialize VertexAI."""
        if self._initialized:
            return
        
        try:
            aiplatform.init(
                project=self.project_id,
                location=self.location
            )
            self._initialized = True
            logger.info(f"VertexAI initialized: {self.project_id} in {self.location}")
        except Exception as e:
            logger.error(f"Failed to initialize VertexAI: {e}")
            raise
    
    def generate_embedding(self, text: str) -> List[float]:
        """Generate embedding for a single text."""
        return self.generate_embeddings([text])[0]
    
    def generate_embeddings(self, texts: List[str]) -> List[List[float]]:
        """Generate embeddings for multiple texts."""
        if not self._initialized:
            self.initialize()
        
        try:
            from vertexai.language_models import TextEmbeddingModel
            
            model = TextEmbeddingModel.from_pretrained(self.model_name)
            
            # Generate embeddings with dimensionality control
            embeddings = model.get_embeddings(
                texts,
                output_dimensionality=self.dimensions
            )
            
            # Extract embedding values
            result = [emb.values for emb in embeddings]
            
            logger.info(f"Generated {len(result)} embeddings")
            return result
            
        except Exception as e:
            logger.error(f"Failed to generate embeddings: {e}")
            raise
    
    def create_product_embedding_text(self, product_data: dict) -> str:
        """
        Create optimized text for embedding generation from product data.
        Combines key product attributes for semantic search.
        """
        parts = []
        
        # Product name and brand
        if product_data.get("name"):
            parts.append(product_data["name"])
        if product_data.get("brand"):
            parts.append(f"Brand: {product_data['brand']}")
        
        # Category information
        if product_data.get("category"):
            cat = product_data["category"]
            if isinstance(cat, dict):
                parts.append(f"Category: {cat.get('primary', '')} {cat.get('subcategory', '')}")
            else:
                parts.append(f"Category: {cat}")
        
        # Descriptions
        if product_data.get("description"):
            parts.append(product_data["description"])
        if product_data.get("long_description"):
            parts.append(product_data["long_description"])
        
        # Key attributes
        if product_data.get("attributes"):
            attrs = product_data["attributes"]
            for key, value in attrs.items():
                if value and key in ["color", "material", "size", "type", "features"]:
                    parts.append(f"{key}: {value}")
        
        # Join all parts
        embedding_text = " | ".join(parts)
        
        # Truncate if too long (model has token limits)
        max_chars = 5000
        if len(embedding_text) > max_chars:
            embedding_text = embedding_text[:max_chars]
        
        return embedding_text


# Global embedding service instance
embedding_service = EmbeddingService()
