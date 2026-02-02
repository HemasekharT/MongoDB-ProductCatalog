#!/usr/bin/env python3
"""Quick script to populate database with sample products (no embeddings)."""

import os
import sys
import random
from datetime import datetime
from pymongo import MongoClient
from dotenv import load_dotenv

load_dotenv()

# Simple product templates
PRODUCTS = [
    {"name": "DeWalt Cordless Drill", "category": "Tools", "price": 129.99, "desc": "20V MAX cordless drill with battery"},
    {"name": "Samsung 55\" Smart TV", "category": "Electronics", "price": 599.99, "desc": "4K UHD Smart TV with HDR"},
    {"name": "Office Chair", "category": "Furniture", "price": 249.99, "desc": "Ergonomic mesh office chair"},
    {"name": "KitchenAid Stand Mixer", "category": "Appliances", "price": 349.99, "desc": "5-quart stand mixer"},
    {"name": "Behr Interior Paint", "category": "Home Improvement", "price": 39.99, "desc": "Premium interior paint, 1 gallon"},
    {"name": "Apple MacBook Pro", "category": "Electronics", "price": 1299.99, "desc": "13-inch laptop with M1 chip"},
    {"name": "Milwaukee Impact Driver", "category": "Tools", "price": 149.99, "desc": "Compact impact driver kit"},
    {"name": "Sectional Sofa", "category": "Furniture", "price": 1299.99, "desc": "L-shaped sectional sofa"},
    {"name": "Dyson Vacuum", "category": "Appliances", "price": 499.99, "desc": "Cordless stick vacuum"},
    {"name": "LED Ceiling Light", "category": "Home Improvement", "price": 59.99, "desc": "Dimmable LED flush mount"},
]

def create_product(template, index):
    """Create a product document."""
    return {
        "product_id": f"SKU-{index:05d}",
        "name": template["name"],
        "description": template["desc"],
        "long_description": template["desc"],
        "category": {
            "primary": template["category"],
            "subcategory": template["category"],
            "department": "General"
        },
        "brand": template["name"].split()[0],
        "price": {
            "current": template["price"],
            "original": template["price"],
            "currency": "USD"
        },
        "attributes": {},
        "inventory": {
            "in_stock": True,
            "quantity": random.randint(10, 100),
            "warehouse_locations": ["WH-01"]
        },
        "images": [f"https://placeholder.com/product-{index}.jpg"],
        "ratings": {
            "average": round(random.uniform(4.0, 5.0), 1),
            "count": random.randint(50, 500)
        },
        "metadata": {
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow(),
            "tags": [template["category"].lower()]
        }
    }

def main():
    """Populate database with sample products."""
    uri = os.getenv('MONGODB_URI')
    if not uri:
        print('❌ MONGODB_URI not found')
        return
    
    try:
        print('🔌 Connecting to MongoDB...')
        client = MongoClient(uri, serverSelectionTimeoutMS=5000)
        db = client['productcatalog']
        collection = db['products']
        
        # Clear existing products
        print('🗑️  Clearing existing products...')
        collection.delete_many({})
        
        # Generate 100 products
        print('📦 Generating products...')
        products = []
        for i in range(100):
            template = PRODUCTS[i % len(PRODUCTS)]
            product = create_product(template, i + 1)
            products.append(product)
        
        # Insert products
        print(f'💾 Inserting {len(products)} products...')
        result = collection.insert_many(products)
        
        print(f'\n✅ Successfully inserted {len(result.inserted_ids)} products!')
        
        # Show stats
        total = collection.count_documents({})
        print(f'\n📊 Database stats:')
        print(f'   Total products: {total}')
        
        # Show categories
        pipeline = [
            {"$group": {"_id": "$category.primary", "count": {"$sum": 1}}},
            {"$sort": {"count": -1}}
        ]
        print(f'\n📂 Products by category:')
        for cat in collection.aggregate(pipeline):
            print(f'   {cat["_id"]}: {cat["count"]}')
        
        client.close()
        
    except Exception as e:
        print(f'❌ Error: {e}')
        return

if __name__ == '__main__':
    main()
