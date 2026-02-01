"""Vector search and RAG implementation using MongoDB Atlas Vector Search."""
from typing import List, Dict, Any, Optional
from backend.services.embeddings import embedding_service
import logging

logger = logging.getLogger(__name__)


class VectorSearchService:
    """Service for vector similarity search and RAG retrieval."""
    
    def __init__(self, collection):
        self.collection = collection
        self.index_name = "product_vector_index"
    
    async def semantic_search(
        self,
        query: str,
        limit: int = 10,
        filters: Optional[Dict[str, Any]] = None
    ) -> List[Dict[str, Any]]:
        """
        Perform semantic vector search using MongoDB Atlas Vector Search.
        
        Args:
            query: Search query text
            limit: Number of results to return
            filters: Optional metadata filters (category, price range, etc.)
        
        Returns:
            List of matching products with similarity scores
        """
        try:
            # Generate embedding for the query
            query_embedding = embedding_service.generate_embedding(query)
            
            # Build vector search pipeline
            pipeline = []
            
            # Vector search stage
            vector_search_stage = {
                "$vectorSearch": {
                    "index": self.index_name,
                    "path": "embedding",
                    "queryVector": query_embedding,
                    "numCandidates": limit * 10,  # Oversample for better results
                    "limit": limit
                }
            }
            
            # Add filters if provided
            if filters:
                filter_conditions = self._build_filter_conditions(filters)
                if filter_conditions:
                    vector_search_stage["$vectorSearch"]["filter"] = filter_conditions
            
            pipeline.append(vector_search_stage)
            
            # Add score projection
            pipeline.append({
                "$project": {
                    "_id": 1,
                    "product_id": 1,
                    "name": 1,
                    "description": 1,
                    "long_description": 1,
                    "category": 1,
                    "brand": 1,
                    "price": 1,
                    "attributes": 1,
                    "inventory": 1,
                    "images": 1,
                    "ratings": 1,
                    "score": {"$meta": "vectorSearchScore"}
                }
            })
            
            # Execute search
            results = await self.collection.aggregate(pipeline).to_list(length=limit)
            
            logger.info(f"Vector search returned {len(results)} results for query: {query}")
            return results
            
        except Exception as e:
            logger.error(f"Vector search failed: {e}")
            raise
    
    async def hybrid_search(
        self,
        query: str,
        limit: int = 10,
        filters: Optional[Dict[str, Any]] = None,
        text_weight: float = 0.3,
        vector_weight: float = 0.7
    ) -> List[Dict[str, Any]]:
        """
        Hybrid search combining semantic vector search with keyword search.
        
        This implements best practice RAG retrieval strategy by combining:
        - Semantic understanding (vector search)
        - Exact keyword matching (text search)
        - Metadata filtering
        """
        try:
            # Get vector search results
            vector_results = await self.semantic_search(query, limit * 2, filters)
            
            # Get text search results
            text_results = await self._text_search(query, limit * 2, filters)
            
            # Combine and rerank results
            combined = self._combine_and_rerank(
                vector_results,
                text_results,
                vector_weight,
                text_weight
            )
            
            return combined[:limit]
            
        except Exception as e:
            logger.error(f"Hybrid search failed: {e}")
            raise
    
    async def _text_search(
        self,
        query: str,
        limit: int,
        filters: Optional[Dict[str, Any]] = None
    ) -> List[Dict[str, Any]]:
        """Perform traditional text search on product fields."""
        try:
            # Build text search query
            search_conditions = {
                "$or": [
                    {"name": {"$regex": query, "$options": "i"}},
                    {"description": {"$regex": query, "$options": "i"}},
                    {"brand": {"$regex": query, "$options": "i"}},
                    {"category.primary": {"$regex": query, "$options": "i"}},
                    {"category.subcategory": {"$regex": query, "$options": "i"}}
                ]
            }
            
            # Add filters
            if filters:
                filter_conditions = self._build_filter_conditions(filters)
                if filter_conditions:
                    search_conditions = {"$and": [search_conditions, filter_conditions]}
            
            # Execute search
            results = await self.collection.find(search_conditions).limit(limit).to_list(length=limit)
            
            # Add text match score (simple relevance)
            for result in results:
                result["score"] = self._calculate_text_score(result, query)
            
            return results
            
        except Exception as e:
            logger.error(f"Text search failed: {e}")
            return []
    
    def _build_filter_conditions(self, filters: Dict[str, Any]) -> Dict[str, Any]:
        """Build MongoDB filter conditions from filter dictionary."""
        conditions = {}
        
        if "category" in filters:
            conditions["category.primary"] = filters["category"]
        
        if "brand" in filters:
            conditions["brand"] = filters["brand"]
        
        if "in_stock" in filters:
            conditions["inventory.in_stock"] = filters["in_stock"]
        
        if "min_price" in filters or "max_price" in filters:
            price_conditions = {}
            if "min_price" in filters:
                price_conditions["$gte"] = filters["min_price"]
            if "max_price" in filters:
                price_conditions["$lte"] = filters["max_price"]
            conditions["price.current"] = price_conditions
        
        if "min_rating" in filters:
            conditions["ratings.average"] = {"$gte": filters["min_rating"]}
        
        return conditions
    
    def _calculate_text_score(self, product: Dict[str, Any], query: str) -> float:
        """Calculate simple text relevance score."""
        query_lower = query.lower()
        score = 0.0
        
        # Name match (highest weight)
        if query_lower in product.get("name", "").lower():
            score += 1.0
        
        # Brand match
        if query_lower in product.get("brand", "").lower():
            score += 0.5
        
        # Description match
        if query_lower in product.get("description", "").lower():
            score += 0.3
        
        return score
    
    def _combine_and_rerank(
        self,
        vector_results: List[Dict[str, Any]],
        text_results: List[Dict[str, Any]],
        vector_weight: float,
        text_weight: float
    ) -> List[Dict[str, Any]]:
        """
        Combine results from vector and text search with weighted scoring.
        Implements reciprocal rank fusion for better result quality.
        """
        # Create score maps
        product_scores = {}
        product_data = {}
        
        # Process vector results
        for rank, result in enumerate(vector_results, 1):
            product_id = result["product_id"]
            # Reciprocal rank fusion score
            score = vector_weight * (1.0 / (rank + 60))
            product_scores[product_id] = product_scores.get(product_id, 0) + score
            product_data[product_id] = result
        
        # Process text results
        for rank, result in enumerate(text_results, 1):
            product_id = result["product_id"]
            score = text_weight * (1.0 / (rank + 60))
            product_scores[product_id] = product_scores.get(product_id, 0) + score
            if product_id not in product_data:
                product_data[product_id] = result
        
        # Sort by combined score
        sorted_products = sorted(
            product_scores.items(),
            key=lambda x: x[1],
            reverse=True
        )
        
        # Build final result list
        results = []
        for product_id, score in sorted_products:
            product = product_data[product_id]
            product["combined_score"] = score
            results.append(product)
        
        return results
