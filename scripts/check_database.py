#!/usr/bin/env python3
"""Check MongoDB ProductCatalog database for products."""

import os
import sys
from pymongo import MongoClient
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def check_database():
    """Check MongoDB database for products."""
    uri = os.getenv('MONGODB_URI')
    if not uri:
        print('❌ MONGODB_URI not found in environment')
        return False
    
    try:
        # Connect to MongoDB
        print('🔌 Connecting to MongoDB Atlas...')
        client = MongoClient(uri, serverSelectionTimeoutMS=5000)
        db = client['ProductCatalog']
        
        # Verify connection
        client.server_info()
        print('✅ Connected successfully\n')
        
        # Check products collection
        products_count = db.products.count_documents({})
        print(f'📊 Total products in database: {products_count}')
        
        if products_count > 0:
            # Show sample products
            print('\n📦 Sample products:')
            for i, product in enumerate(db.products.find().limit(3), 1):
                print(f'\n  Product {i}:')
                print(f'    - ID: {product.get("_id")}')
                print(f'    - Name: {product.get("name")}')
                print(f'    - Category: {product.get("category")}')
                print(f'    - Price: ${product.get("price", 0):.2f}')
                print(f'    - In Stock: {product.get("in_stock", False)}')
                print(f'    - Has embedding: {"embedding" in product}')
                if 'embedding' in product:
                    print(f'    - Embedding dimensions: {len(product["embedding"])}')
            
            # Category breakdown
            print('\n📂 Products by category:')
            pipeline = [
                {"$group": {"_id": "$category", "count": {"$sum": 1}}},
                {"$sort": {"count": -1}}
            ]
            for cat in db.products.aggregate(pipeline):
                print(f'  - {cat["_id"]}: {cat["count"]} products')
            
        else:
            print('\n⚠️  No products found in database!')
            print('\nTo populate the database, run:')
            print('  python scripts/generate_products.py')
        
        # Check indexes
        print('\n🔍 Database indexes:')
        indexes = list(db.products.list_indexes())
        for idx in indexes:
            print(f'  - {idx["name"]}')
            if 'key' in idx:
                keys = ', '.join([f'{k}: {v}' for k, v in idx['key'].items()])
                print(f'    Keys: {keys}')
        
        # Check for vector search index
        print('\n🔎 Vector Search Index:')
        print('  Note: Vector search indexes must be created manually in MongoDB Atlas UI')
        print('  See: scripts/setup_indexes.py for instructions')
        
        client.close()
        return products_count > 0
        
    except Exception as e:
        print(f'\n❌ Error connecting to MongoDB: {e}')
        print('\nTroubleshooting:')
        print('  1. Check MONGODB_URI in .env file')
        print('  2. Verify MongoDB Atlas network access allows your IP')
        print('  3. Confirm database credentials are correct')
        return False

if __name__ == '__main__':
    success = check_database()
    sys.exit(0 if success else 1)
