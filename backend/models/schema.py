"""Product schema models for MongoDB."""
from datetime import datetime
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field
from bson import ObjectId


class PyObjectId(ObjectId):
    """Custom ObjectId type for Pydantic."""
    
    @classmethod
    def __get_pydantic_core_schema__(cls, source_type, handler):
        from pydantic_core import core_schema
        return core_schema.union_schema([
            core_schema.is_instance_schema(ObjectId),
            core_schema.chain_schema([
                core_schema.str_schema(),
                core_schema.no_info_plain_validator_function(cls.validate),
            ])
        ],
        serialization=core_schema.plain_serializer_function_ser_schema(
            lambda x: str(x)
        ))

    @classmethod
    def validate(cls, v):
        if isinstance(v, ObjectId):
            return v
        if not ObjectId.is_valid(v):
            raise ValueError("Invalid ObjectId")
        return ObjectId(v)


class PriceInfo(BaseModel):
    """Product pricing information."""
    current: float = Field(..., description="Current price")
    original: float = Field(..., description="Original price")
    currency: str = Field(default="USD", description="Currency code")


class CategoryInfo(BaseModel):
    """Product category information."""
    primary: str = Field(..., description="Primary category")
    subcategory: str = Field(..., description="Subcategory")
    department: str = Field(..., description="Department")


class InventoryInfo(BaseModel):
    """Product inventory information."""
    in_stock: bool = Field(..., description="Stock availability")
    quantity: int = Field(..., description="Available quantity")
    warehouse_locations: List[str] = Field(default_factory=list, description="Warehouse locations")


class RatingInfo(BaseModel):
    """Product rating information."""
    average: float = Field(..., description="Average rating")
    count: int = Field(..., description="Number of ratings")


class MetadataInfo(BaseModel):
    """Product metadata."""
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    tags: List[str] = Field(default_factory=list)


class Product(BaseModel):
    """Complete product model."""
    id: Optional[PyObjectId] = Field(alias="_id", default=None)
    product_id: str = Field(..., description="Unique SKU")
    name: str = Field(..., description="Product name")
    description: str = Field(..., description="Short description")
    long_description: str = Field(..., description="Detailed description")
    category: CategoryInfo
    brand: str = Field(..., description="Brand name")
    price: PriceInfo
    attributes: Dict[str, Any] = Field(default_factory=dict, description="Dynamic attributes")
    inventory: InventoryInfo
    images: List[str] = Field(default_factory=list, description="Image URLs")
    ratings: RatingInfo
    metadata: MetadataInfo = Field(default_factory=MetadataInfo)
    embedding: Optional[List[float]] = Field(default=None, description="Vector embedding")
    embedding_text: Optional[str] = Field(default=None, description="Text used for embedding")

    class Config:
        populate_by_name = True
        arbitrary_types_allowed = True
        json_encoders = {ObjectId: str}


class ProductCreate(BaseModel):
    """Model for creating a new product."""
    product_id: str
    name: str
    description: str
    long_description: str
    category: CategoryInfo
    brand: str
    price: PriceInfo
    attributes: Dict[str, Any] = Field(default_factory=dict)
    inventory: InventoryInfo
    images: List[str] = Field(default_factory=list)
    ratings: RatingInfo = Field(default=RatingInfo(average=0.0, count=0))


class SearchQuery(BaseModel):
    """Model for search queries."""
    query: str = Field(..., description="Search query text")
    limit: int = Field(default=10, description="Number of results")
    filters: Optional[Dict[str, Any]] = Field(default=None, description="Additional filters")


class ChatMessage(BaseModel):
    """Model for chat messages."""
    message: str = Field(..., description="User message")
    conversation_id: Optional[str] = Field(default=None, description="Conversation ID")
