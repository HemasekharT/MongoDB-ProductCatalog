"""Database configuration and connection management."""
import os
from motor.motor_asyncio import AsyncIOMotorClient
from pymongo import MongoClient
from typing import Optional
import logging

logger = logging.getLogger(__name__)


class DatabaseManager:
    """Manages MongoDB Atlas connections."""
    
    def __init__(self):
        self.client: Optional[AsyncIOMotorClient] = None
        self.db = None
        self.sync_client: Optional[MongoClient] = None
        self.sync_db = None
        
    async def connect(self):
        """Establish async connection to MongoDB Atlas."""
        mongodb_uri = os.getenv("MONGODB_URI")
        db_name = os.getenv("MONGODB_DB_NAME", "product_catalog")
        
        if not mongodb_uri:
            raise ValueError("MONGODB_URI environment variable not set")
        
        try:
            self.client = AsyncIOMotorClient(mongodb_uri)
            self.db = self.client[db_name]
            
            # Test connection
            await self.client.admin.command('ping')
            logger.info(f"Successfully connected to MongoDB Atlas database: {db_name}")
            
        except Exception as e:
            logger.error(f"Failed to connect to MongoDB: {e}")
            raise
    
    def connect_sync(self):
        """Establish synchronous connection for scripts."""
        mongodb_uri = os.getenv("MONGODB_URI")
        db_name = os.getenv("MONGODB_DB_NAME", "product_catalog")
        
        if not mongodb_uri:
            raise ValueError("MONGODB_URI environment variable not set")
        
        try:
            self.sync_client = MongoClient(mongodb_uri)
            self.sync_db = self.sync_client[db_name]
            
            # Test connection
            self.sync_client.admin.command('ping')
            logger.info(f"Successfully connected to MongoDB Atlas (sync): {db_name}")
            
        except Exception as e:
            logger.error(f"Failed to connect to MongoDB: {e}")
            raise
    
    async def close(self):
        """Close async connection."""
        if self.client:
            self.client.close()
            logger.info("MongoDB connection closed")
    
    def close_sync(self):
        """Close sync connection."""
        if self.sync_client:
            self.sync_client.close()
            logger.info("MongoDB sync connection closed")
    
    def get_collection(self, collection_name: str):
        """Get a collection from the database."""
        if self.db is None:
            raise RuntimeError("Database not connected. Call connect() first.")
        return self.db[collection_name]
    
    def get_collection_sync(self, collection_name: str):
        """Get a collection from the sync database."""
        if self.sync_db is None:
            raise RuntimeError("Database not connected. Call connect_sync() first.")
        return self.sync_db[collection_name]


# Global database manager instance
db_manager = DatabaseManager()


async def get_database():
    """Dependency for FastAPI routes."""
    if db_manager.db is None:
        await db_manager.connect()
    return db_manager.db
