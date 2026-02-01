"""FastAPI main application."""
import os
from contextlib import asynccontextmanager
from fastapi import FastAPI, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv
import logging
from typing import List, Optional
from bson import ObjectId

from backend.config.database import db_manager, get_database
from backend.models.schema import Product, ProductCreate, SearchQuery, ChatMessage
from backend.services.embeddings import embedding_service
from backend.services.vector_search import VectorSearchService
from backend.services.vertex_agent import ProductCatalogAgent

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def serialize_doc(doc):
    """Convert MongoDB document to JSON-serializable dict."""
    if doc is None:
        return None
    if isinstance(doc, list):
        return [serialize_doc(item) for item in doc]
    if isinstance(doc, dict):
        return {key: serialize_doc(value) for key, value in doc.items()}
    if isinstance(doc, ObjectId):
        return str(doc)
    return doc


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager."""
    # Startup
    logger.info("Starting Product Catalog API...")
    
    # Try to connect to MongoDB, but don't fail startup if it doesn't work
    try:
        await db_manager.connect()
        logger.info("MongoDB connected successfully")
    except Exception as e:
        logger.error(f"MongoDB connection failed (will retry on requests): {e}")
        # Don't raise - allow the app to start anyway for Cloud Run health checks
    
    # Initialize VertexAI
    try:
        embedding_service.initialize()
        logger.info("VertexAI initialized successfully")
    except Exception as e:
        logger.error(f"VertexAI initialization failed: {e}")
    
    logger.info("Application started successfully")
    
    yield
    
    # Shutdown
    logger.info("Shutting down...")
    if db_manager.client is not None:
        await db_manager.close()


# Create FastAPI app
app = FastAPI(
    title="Product Catalog API",
    description="MongoDB-based product catalog with VertexAI agent and vector search",
    version="1.0.0",
    lifespan=lifespan
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify exact origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Health check
@app.get("/")
async def root():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "service": "Product Catalog API",
        "version": "1.0.0"
    }


# Product endpoints
@app.post("/api/products", response_model=Product)
async def create_product(
    product: ProductCreate,
    db = Depends(get_database)
):
    """Create a new product with embedding."""
    try:
        collection = db["products"]
        
        # Convert to dict
        product_dict = product.model_dump()
        
        # Generate embedding
        embedding_text = embedding_service.create_product_embedding_text(product_dict)
        embedding = embedding_service.generate_embedding(embedding_text)
        
        product_dict["embedding"] = embedding
        product_dict["embedding_text"] = embedding_text
        
        # Insert into database
        result = await collection.insert_one(product_dict)
        
        # Fetch and return created product
        created_product = await collection.find_one({"_id": result.inserted_id})
        
        logger.info(f"Created product: {product.product_id}")
        return Product(**created_product)
        
    except Exception as e:
        logger.error(f"Failed to create product: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/products/{product_id}")
async def get_product(
    product_id: str,
    db = Depends(get_database)
):
    """Get a product by ID."""
    try:
        collection = db["products"]
        product = await collection.find_one({"product_id": product_id})
        
        if not product:
            raise HTTPException(status_code=404, detail="Product not found")
        
        return serialize_doc(product)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get product: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/products")
async def list_products(
    skip: int = 0,
    limit: int = 20,
    category: Optional[str] = None,
    db = Depends(get_database)
):
    """List products with optional filtering."""
    try:
        collection = db["products"]
        
        # Build query
        query = {}
        if category:
            query["category.primary"] = category
        
        # Execute query
        products = await collection.find(query).skip(skip).limit(limit).to_list(length=limit)
        
        return {
            "products": serialize_doc(products),
            "count": len(products),
            "skip": skip,
            "limit": limit
        }
        
    except Exception as e:
        logger.error(f"Failed to list products: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/products/search")
async def search_products(
    query: SearchQuery,
    db = Depends(get_database)
):
    """Traditional keyword search."""
    try:
        collection = db["products"]
        
        # Build search query
        search_conditions = {
            "$or": [
                {"name": {"$regex": query.query, "$options": "i"}},
                {"description": {"$regex": query.query, "$options": "i"}},
                {"brand": {"$regex": query.query, "$options": "i"}}
            ]
        }
        
        # Execute search
        results = await collection.find(search_conditions).limit(query.limit).to_list(length=query.limit)
        
        return {
            "query": query.query,
            "results": serialize_doc(results),
            "count": len(results)
        }
        
    except Exception as e:
        logger.error(f"Search failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/products/semantic-search")
async def semantic_search(
    query: SearchQuery,
    db = Depends(get_database)
):
    """Semantic vector search."""
    try:
        collection = db["products"]
        vector_search = VectorSearchService(collection)
        
        results = await vector_search.semantic_search(
            query=query.query,
            limit=query.limit,
            filters=query.filters
        )
        
        return {
            "query": query.query,
            "results": serialize_doc(results),
            "count": len(results)
        }
        
    except Exception as e:
        logger.error(f"Semantic search failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/products/hybrid-search")
async def hybrid_search(
    query: SearchQuery,
    db = Depends(get_database)
):
    """Hybrid search combining semantic and keyword search."""
    try:
        collection = db["products"]
        vector_search = VectorSearchService(collection)
        
        results = await vector_search.hybrid_search(
            query=query.query,
            limit=query.limit,
            filters=query.filters
        )
        
        return {
            "query": query.query,
            "results": serialize_doc(results),
            "count": len(results)
        }
        
    except Exception as e:
        logger.error(f"Hybrid search failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/chat")
async def chat_with_agent(
    message: ChatMessage,
    db = Depends(get_database)
):
    """Chat with VertexAI agent for conversational product search."""
    try:
        collection = db["products"]
        vector_search = VectorSearchService(collection)
        agent = ProductCatalogAgent(vector_search)
        
        response = await agent.chat(message.message)
        
        return serialize_doc(response)
        
    except Exception as e:
        logger.error(f"Agent chat failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


if __name__ == "__main__":
    import uvicorn
    
    host = os.getenv("API_HOST", "0.0.0.0")
    port = int(os.getenv("API_PORT", 8000))
    
    uvicorn.run(app, host=host, port=port)
