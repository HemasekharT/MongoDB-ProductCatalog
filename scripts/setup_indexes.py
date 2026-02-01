"""Setup MongoDB Atlas Vector Search indexes."""
import os
import sys
from dotenv import load_dotenv
import logging

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from backend.config.database import db_manager

# Load environment variables
load_dotenv()

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def create_vector_search_index():
    """Create vector search index on products collection."""
    try:
        # Connect to database
        db_manager.connect_sync()
        db = db_manager.sync_db
        
        # Get products collection
        collection = db["products"]
        
        # Vector search index definition
        index_definition = {
            "fields": [
                {
                    "type": "vector",
                    "path": "embedding",
                    "numDimensions": 768,
                    "similarity": "cosine"
                },
                {
                    "type": "filter",
                    "path": "category.primary"
                },
                {
                    "type": "filter",
                    "path": "brand"
                },
                {
                    "type": "filter",
                    "path": "price.current"
                },
                {
                    "type": "filter",
                    "path": "inventory.in_stock"
                },
                {
                    "type": "filter",
                    "path": "ratings.average"
                }
            ]
        }
        
        logger.info("Creating vector search index...")
        logger.info("Note: Vector search indexes must be created through MongoDB Atlas UI")
        logger.info("Index definition:")
        logger.info(f"  Index Name: product_vector_index")
        logger.info(f"  Collection: products")
        logger.info(f"  Definition: {index_definition}")
        
        # Create traditional indexes
        logger.info("\nCreating traditional indexes...")
        
        # Product ID index (unique)
        collection.create_index("product_id", unique=True)
        logger.info("✓ Created index on product_id")
        
        # Category index
        collection.create_index("category.primary")
        logger.info("✓ Created index on category.primary")
        
        # Brand index
        collection.create_index("brand")
        logger.info("✓ Created index on brand")
        
        # Price index
        collection.create_index("price.current")
        logger.info("✓ Created index on price.current")
        
        # Stock index
        collection.create_index("inventory.in_stock")
        logger.info("✓ Created index on inventory.in_stock")
        
        # Compound index for common queries
        collection.create_index([
            ("category.primary", 1),
            ("price.current", 1),
            ("inventory.in_stock", 1)
        ])
        logger.info("✓ Created compound index on category, price, stock")
        
        logger.info("\n" + "="*60)
        logger.info("IMPORTANT: Vector Search Index Setup")
        logger.info("="*60)
        logger.info("\nTo complete the setup, create a Vector Search index in MongoDB Atlas:")
        logger.info("\n1. Go to MongoDB Atlas → Database → Search")
        logger.info("2. Click 'Create Search Index'")
        logger.info("3. Choose 'JSON Editor'")
        logger.info("4. Use this configuration:\n")
        logger.info("""{
  "fields": [
    {
      "type": "vector",
      "path": "embedding",
      "numDimensions": 768,
      "similarity": "cosine"
    },
    {
      "type": "filter",
      "path": "category.primary"
    },
    {
      "type": "filter",
      "path": "brand"
    },
    {
      "type": "filter",
      "path": "price.current"
    },
    {
      "type": "filter",
      "path": "inventory.in_stock"
    }
  ]
}""")
        logger.info("\n5. Name the index: product_vector_index")
        logger.info("6. Select collection: products")
        logger.info("7. Click 'Create Search Index'")
        logger.info("\n" + "="*60)
        
        db_manager.close_sync()
        
    except Exception as e:
        logger.error(f"Failed to create indexes: {e}")
        raise


if __name__ == "__main__":
    create_vector_search_index()
