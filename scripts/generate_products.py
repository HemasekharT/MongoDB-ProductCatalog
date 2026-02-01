"""Generate realistic product data for the catalog."""
import os
import sys
import random
from datetime import datetime
from dotenv import load_dotenv
import logging

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from backend.config.database import db_manager
from backend.services.embeddings import embedding_service

# Load environment variables
load_dotenv()

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


# Product data templates
CATEGORIES = {
    "Tools": {
        "subcategories": ["Power Tools", "Hand Tools", "Tool Storage", "Accessories"],
        "brands": ["DeWalt", "Milwaukee", "Makita", "Bosch", "Craftsman", "Stanley"],
        "products": [
            {
                "name": "Cordless Drill Driver Kit",
                "desc": "20V MAX lithium-ion cordless drill with 2 batteries",
                "long_desc": "Professional-grade cordless drill with brushless motor, 2-speed transmission, and LED work light. Includes 2 batteries, charger, and carrying case.",
                "price_range": (89, 199),
                "attributes": {"voltage": "20V", "battery_type": "Lithium-Ion", "chuck_size": "1/2 inch"}
            },
            {
                "name": "Circular Saw",
                "desc": "7-1/4 inch circular saw with laser guide",
                "long_desc": "Powerful 15-amp motor circular saw with electric brake, bevel capacity up to 56 degrees, and dust blower to keep cut line clear.",
                "price_range": (69, 149),
                "attributes": {"blade_size": "7-1/4 inch", "motor": "15 amp", "features": "laser guide"}
            },
            {
                "name": "Impact Driver",
                "desc": "Compact impact driver for fastening applications",
                "long_desc": "High-torque impact driver with variable speed trigger and LED light. Perfect for driving screws and bolts in tight spaces.",
                "price_range": (79, 169),
                "attributes": {"max_torque": "1500 in-lbs", "speed": "0-3200 RPM", "weight": "2.8 lbs"}
            },
            {
                "name": "Hammer Drill",
                "desc": "Corded hammer drill for concrete and masonry",
                "long_desc": "Heavy-duty hammer drill with 8.5 amp motor, variable speed, and depth gauge. Ideal for drilling into concrete, brick, and stone.",
                "price_range": (59, 129),
                "attributes": {"motor": "8.5 amp", "chuck": "1/2 inch", "modes": "drill, hammer drill"}
            },
            {
                "name": "Reciprocating Saw",
                "desc": "Variable speed reciprocating saw for demolition",
                "long_desc": "Powerful reciprocating saw with tool-free blade change, adjustable shoe, and variable speed trigger for cutting wood, metal, and plastic.",
                "price_range": (79, 159),
                "attributes": {"stroke_length": "1-1/8 inch", "speed": "0-3000 SPM", "weight": "7 lbs"}
            }
        ]
    },
    "Electronics": {
        "subcategories": ["Computers", "Smartphones", "Tablets", "Accessories"],
        "brands": ["Apple", "Samsung", "Dell", "HP", "Lenovo", "Asus"],
        "products": [
            {
                "name": "Laptop Computer",
                "desc": "15.6-inch laptop with Intel Core i5 processor",
                "long_desc": "High-performance laptop with 8GB RAM, 256GB SSD, Full HD display, and Windows 11. Perfect for work and entertainment.",
                "price_range": (499, 899),
                "attributes": {"processor": "Intel Core i5", "ram": "8GB", "storage": "256GB SSD", "screen": "15.6 inch"}
            },
            {
                "name": "Wireless Earbuds",
                "desc": "True wireless earbuds with active noise cancellation",
                "long_desc": "Premium wireless earbuds with ANC, transparency mode, and up to 24 hours battery life with charging case.",
                "price_range": (99, 249),
                "attributes": {"battery_life": "24 hours", "features": "ANC, transparency mode", "connectivity": "Bluetooth 5.0"}
            },
            {
                "name": "Smart Watch",
                "desc": "Fitness tracker smartwatch with heart rate monitor",
                "long_desc": "Advanced smartwatch with GPS, heart rate monitoring, sleep tracking, and 5-day battery life. Water resistant up to 50m.",
                "price_range": (149, 399),
                "attributes": {"display": "AMOLED", "battery": "5 days", "water_resistance": "50m"}
            },
            {
                "name": "Tablet",
                "desc": "10.5-inch tablet with stylus support",
                "long_desc": "Versatile tablet with high-resolution display, quad-core processor, and support for stylus input. Great for creativity and productivity.",
                "price_range": (299, 599),
                "attributes": {"screen_size": "10.5 inch", "storage": "64GB", "stylus": "included"}
            }
        ]
    },
    "Furniture": {
        "subcategories": ["Living Room", "Bedroom", "Office", "Outdoor"],
        "brands": ["Ashley", "IKEA", "Wayfair", "West Elm", "Pottery Barn"],
        "products": [
            {
                "name": "Ergonomic Office Chair",
                "desc": "Mesh back office chair with lumbar support",
                "long_desc": "Professional office chair with breathable mesh back, adjustable lumbar support, armrests, and seat height. Weight capacity 300 lbs.",
                "price_range": (149, 399),
                "attributes": {"material": "mesh", "adjustable": "yes", "weight_capacity": "300 lbs"}
            },
            {
                "name": "Standing Desk",
                "desc": "Electric height-adjustable standing desk",
                "long_desc": "Motorized standing desk with memory presets, cable management, and sturdy steel frame. Desktop size 60x30 inches.",
                "price_range": (299, 699),
                "attributes": {"size": "60x30 inches", "height_range": "28-48 inches", "motor": "dual motor"}
            },
            {
                "name": "Sectional Sofa",
                "desc": "L-shaped sectional sofa with chaise",
                "long_desc": "Modern sectional sofa with deep seats, plush cushions, and durable upholstery. Seats 5-6 people comfortably.",
                "price_range": (799, 1899),
                "attributes": {"seating": "5-6 people", "material": "fabric", "configuration": "L-shaped"}
            },
            {
                "name": "Patio Dining Set",
                "desc": "7-piece outdoor dining set with umbrella",
                "long_desc": "Weather-resistant patio dining set includes table, 6 chairs, and umbrella. Powder-coated steel frame with tempered glass table top.",
                "price_range": (399, 899),
                "attributes": {"pieces": "7", "material": "steel, glass", "weather_resistant": "yes"}
            }
        ]
    },
    "Appliances": {
        "subcategories": ["Kitchen", "Laundry", "Cleaning", "Small Appliances"],
        "brands": ["Whirlpool", "LG", "Samsung", "GE", "KitchenAid", "Dyson"],
        "products": [
            {
                "name": "French Door Refrigerator",
                "desc": "25 cu ft stainless steel refrigerator with ice maker",
                "long_desc": "Energy-efficient French door refrigerator with LED lighting, adjustable shelves, humidity-controlled crispers, and external ice/water dispenser.",
                "price_range": (1299, 2499),
                "attributes": {"capacity": "25 cu ft", "finish": "stainless steel", "ice_maker": "yes"}
            },
            {
                "name": "Front Load Washer",
                "desc": "4.5 cu ft front load washing machine",
                "long_desc": "High-efficiency front load washer with steam clean, allergen cycle, and vibration reduction. Energy Star certified.",
                "price_range": (699, 1299),
                "attributes": {"capacity": "4.5 cu ft", "energy_star": "yes", "features": "steam clean"}
            },
            {
                "name": "Cordless Vacuum",
                "desc": "Stick vacuum with powerful suction and long battery",
                "long_desc": "Lightweight cordless vacuum with HEPA filtration, LED display, and up to 60 minutes runtime. Converts to handheld.",
                "price_range": (299, 699),
                "attributes": {"battery": "60 minutes", "filtration": "HEPA", "weight": "6 lbs"}
            },
            {
                "name": "Stand Mixer",
                "desc": "5-quart tilt-head stand mixer with attachments",
                "long_desc": "Professional stand mixer with 10 speeds, 5-quart stainless steel bowl, and includes dough hook, flat beater, and wire whip.",
                "price_range": (199, 449),
                "attributes": {"capacity": "5 quart", "speeds": "10", "attachments": "3 included"}
            }
        ]
    },
    "Home Improvement": {
        "subcategories": ["Paint", "Hardware", "Lighting", "Plumbing"],
        "brands": ["Behr", "Sherwin-Williams", "Schlage", "Moen", "Kohler"],
        "products": [
            {
                "name": "Interior Paint",
                "desc": "Premium interior paint with primer, 1 gallon",
                "long_desc": "Low-VOC interior paint and primer in one. Excellent coverage, washable finish, and available in 200+ colors.",
                "price_range": (29, 59),
                "attributes": {"coverage": "400 sq ft", "finish": "eggshell", "voc": "low"}
            },
            {
                "name": "LED Ceiling Light",
                "desc": "Flush mount LED ceiling light, dimmable",
                "long_desc": "Energy-efficient LED ceiling light with 3000K warm white, dimmable, and easy installation. 50,000 hour lifespan.",
                "price_range": (39, 89),
                "attributes": {"lumens": "2000", "color_temp": "3000K", "dimmable": "yes"}
            },
            {
                "name": "Kitchen Faucet",
                "desc": "Pull-down kitchen faucet with spray function",
                "long_desc": "Single-handle kitchen faucet with pull-down sprayer, magnetic docking, and spot-resistant finish. Easy to install.",
                "price_range": (89, 249),
                "attributes": {"finish": "stainless", "spray_modes": "2", "installation": "1-hole"}
            }
        ]
    }
}


def generate_products(num_products: int = 500):
    """Generate realistic product data."""
    products = []
    
    for i in range(num_products):
        # Select random category
        category_name = random.choice(list(CATEGORIES.keys()))
        category_data = CATEGORIES[category_name]
        
        # Select random subcategory and brand
        subcategory = random.choice(category_data["subcategories"])
        brand = random.choice(category_data["brands"])
        
        # Select random product template
        product_template = random.choice(category_data["products"])
        
        # Generate product
        product_id = f"SKU-{category_name[:3].upper()}-{i+1:05d}"
        
        # Add variation to name
        name = f"{brand} {product_template['name']}"
        
        # Generate price
        price_min, price_max = product_template["price_range"]
        original_price = round(random.uniform(price_min, price_max), 2)
        
        # Random discount
        has_discount = random.random() < 0.3  # 30% chance of discount
        current_price = round(original_price * random.uniform(0.7, 0.95), 2) if has_discount else original_price
        
        # Inventory
        in_stock = random.random() < 0.85  # 85% in stock
        quantity = random.randint(0, 100) if in_stock else 0
        
        # Ratings
        avg_rating = round(random.uniform(3.5, 5.0), 1)
        rating_count = random.randint(10, 500)
        
        # Images (placeholder URLs)
        num_images = random.randint(1, 4)
        images = [f"https://placeholder.com/product-{product_id}-{j}.jpg" for j in range(num_images)]
        
        product = {
            "product_id": product_id,
            "name": name,
            "description": product_template["desc"],
            "long_description": product_template["long_desc"],
            "category": {
                "primary": category_name,
                "subcategory": subcategory,
                "department": "General"
            },
            "brand": brand,
            "price": {
                "current": current_price,
                "original": original_price,
                "currency": "USD"
            },
            "attributes": product_template["attributes"],
            "inventory": {
                "in_stock": in_stock,
                "quantity": quantity,
                "warehouse_locations": ["WH-01", "WH-02"] if in_stock else []
            },
            "images": images,
            "ratings": {
                "average": avg_rating,
                "count": rating_count
            },
            "metadata": {
                "created_at": datetime.utcnow(),
                "updated_at": datetime.utcnow(),
                "tags": [category_name.lower(), subcategory.lower(), brand.lower()]
            }
        }
        
        products.append(product)
    
    return products


def insert_products_with_embeddings(products, batch_size=10):
    """Insert products into MongoDB with embeddings."""
    try:
        # Connect to database
        db_manager.connect_sync()
        db = db_manager.sync_db
        collection = db["products"]
        
        # Initialize embedding service
        embedding_service.initialize()
        
        logger.info(f"Generating embeddings and inserting {len(products)} products...")
        
        # Process in batches
        for i in range(0, len(products), batch_size):
            batch = products[i:i+batch_size]
            
            # Generate embedding texts
            embedding_texts = []
            for product in batch:
                embedding_text = embedding_service.create_product_embedding_text(product)
                product["embedding_text"] = embedding_text
                embedding_texts.append(embedding_text)
            
            # Generate embeddings
            embeddings = embedding_service.generate_embeddings(embedding_texts)
            
            # Add embeddings to products
            for product, embedding in zip(batch, embeddings):
                product["embedding"] = embedding
            
            # Insert batch
            collection.insert_many(batch)
            
            logger.info(f"Inserted batch {i//batch_size + 1}/{(len(products)-1)//batch_size + 1}")
        
        logger.info(f"✓ Successfully inserted {len(products)} products with embeddings")
        
        # Print statistics
        total_count = collection.count_documents({})
        in_stock_count = collection.count_documents({"inventory.in_stock": True})
        
        logger.info(f"\nDatabase Statistics:")
        logger.info(f"  Total products: {total_count}")
        logger.info(f"  In stock: {in_stock_count}")
        logger.info(f"  Out of stock: {total_count - in_stock_count}")
        
        # Category breakdown
        logger.info(f"\nProducts by category:")
        for category in CATEGORIES.keys():
            count = collection.count_documents({"category.primary": category})
            logger.info(f"  {category}: {count}")
        
        db_manager.close_sync()
        
    except Exception as e:
        logger.error(f"Failed to insert products: {e}")
        raise


if __name__ == "__main__":
    logger.info("Generating product data...")
    products = generate_products(500)
    
    logger.info(f"Generated {len(products)} products")
    logger.info("Inserting into MongoDB with embeddings...")
    
    insert_products_with_embeddings(products)
    
    logger.info("\n✓ Product generation complete!")
