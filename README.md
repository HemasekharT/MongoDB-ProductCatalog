# Product Catalog with MongoDB Atlas Vector Search & VertexAI Agent

A comprehensive retail product catalog system powered by MongoDB Atlas with Vector Search capabilities for semantic product discovery, and a VertexAI agent for conversational product search and recommendations.

## 🌟 Features

### Core Capabilities
- **MongoDB Atlas Vector Search**: Semantic product search using 768-dimensional embeddings
- **VertexAI Agent Integration**: Conversational AI assistant powered by Gemini 1.5 Pro
- **Hybrid Search**: Combines semantic vector search with traditional keyword matching
- **RAG Implementation**: Retrieval-Augmented Generation with contextual retrieval strategies
- **Real-time Product Catalog**: 500+ realistic products across 5 major categories

### Search Modes
1. **Semantic Search**: AI-powered understanding of product queries
2. **Hybrid Search**: Best of both worlds - semantic + keyword matching
3. **Keyword Search**: Traditional text-based search

### AI Agent Tools
- `search_products`: Semantic product discovery
- `filter_by_category`: Category-based filtering
- `filter_by_price_range`: Price range filtering
- `check_availability`: Stock availability checking

## 🏗️ Architecture

```
┌─────────────────┐
│   Frontend      │
│  (HTML/CSS/JS)  │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  FastAPI        │
│  Backend        │
└────────┬────────┘
         │
    ┌────┴─────┬──────────────┐
    ▼          ▼              ▼
┌────────┐ ┌─────────┐  ┌──────────┐
│MongoDB │ │VertexAI │  │VertexAI  │
│ Atlas  │ │Embedding│  │  Agent   │
│Vector  │ │ Service │  │ (Gemini) │
│Search  │ └─────────┘  └──────────┘
└────────┘
```

## 📋 Prerequisites

- **Python 3.9+**
- **MongoDB Atlas Account** (free tier available)
- **Google Cloud Project** with VertexAI API enabled
- **Service Account** with VertexAI permissions

## 🚀 Quick Start

### 1. Clone and Setup

```bash
cd MongoDB-ProductCatalog
cp .env.example .env
```

### 2. Configure Environment Variables

Edit `.env` with your credentials:

```bash
# MongoDB Atlas
MONGODB_URI=mongodb+srv://username:password@cluster.mongodb.net/?retryWrites=true&w=majority
MONGODB_DB_NAME=product_catalog

# Google Cloud
GOOGLE_CLOUD_PROJECT=your-project-id
GOOGLE_APPLICATION_CREDENTIALS=/path/to/service-account.json
VERTEX_AI_LOCATION=us-central1
```

### 3. Install Dependencies

```bash
pip install -r requirements.txt
```

### 4. Setup Database

```bash
# Create indexes
python scripts/setup_indexes.py

# Generate sample products (500+ items)
python scripts/generate_products.py
```

**Important**: After running `setup_indexes.py`, you must create the Vector Search index in MongoDB Atlas UI:

1. Go to MongoDB Atlas → Database → Search
2. Click "Create Search Index"
3. Choose "JSON Editor"
4. Use this configuration:

```json
{
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
}
```

5. Name the index: `product_vector_index`
6. Select collection: `products`

### 5. Start the Backend

```bash
cd backend
uvicorn main:app --reload --port 8000
```

The API will be available at `http://localhost:8000`

### 6. Start the Frontend

```bash
cd frontend
python -m http.server 3000
```

Open your browser to `http://localhost:3000`

## 📚 API Documentation

### Product Endpoints

#### List Products
```bash
GET /api/products?skip=0&limit=20&category=Tools
```

#### Get Product by ID
```bash
GET /api/products/{product_id}
```

#### Create Product
```bash
POST /api/products
Content-Type: application/json

{
  "product_id": "SKU-001",
  "name": "Cordless Drill",
  "description": "20V drill with battery",
  "long_description": "Professional grade...",
  "category": {
    "primary": "Tools",
    "subcategory": "Power Tools",
    "department": "General"
  },
  "brand": "DeWalt",
  "price": {
    "current": 149.99,
    "original": 199.99,
    "currency": "USD"
  },
  "attributes": {
    "voltage": "20V",
    "battery_type": "Lithium-Ion"
  },
  "inventory": {
    "in_stock": true,
    "quantity": 50,
    "warehouse_locations": ["WH-01"]
  },
  "images": ["https://example.com/image.jpg"],
  "ratings": {
    "average": 4.5,
    "count": 120
  }
}
```

### Search Endpoints

#### Semantic Search
```bash
POST /api/products/semantic-search
Content-Type: application/json

{
  "query": "tools for home renovation",
  "limit": 10,
  "filters": {
    "category": "Tools",
    "min_price": 50,
    "max_price": 200,
    "in_stock": true
  }
}
```

#### Hybrid Search
```bash
POST /api/products/hybrid-search
Content-Type: application/json

{
  "query": "cordless power drill",
  "limit": 10
}
```

#### Keyword Search
```bash
POST /api/products/search
Content-Type: application/json

{
  "query": "drill",
  "limit": 10
}
```

### AI Agent Endpoint

#### Chat with Agent
```bash
POST /api/chat
Content-Type: application/json

{
  "message": "I need a drill for home projects under $100"
}
```

Response:
```json
{
  "response": "I found 3 drills under $100 for you...",
  "products": [...],
  "function_calls": [...]
}
```

## 🎯 RAG Implementation Details

### Contextual Retrieval Strategy

Our RAG implementation uses a **hybrid search approach** combining:

1. **Semantic Vector Search**: MongoDB Atlas Vector Search with 768-dim embeddings
2. **Keyword Matching**: Traditional text search on product fields
3. **Metadata Filtering**: Category, price, brand, stock filters
4. **Reciprocal Rank Fusion**: Combines results from multiple sources
5. **Reranking**: Cross-encoder for result refinement

### Embedding Generation

Products are embedded using VertexAI `text-embedding-004` model with:
- **Dimensions**: 768
- **Input**: Combined product name, brand, category, description, and key attributes
- **Similarity**: Cosine similarity for vector search

### Vector Search Pipeline

```python
{
  "$vectorSearch": {
    "index": "product_vector_index",
    "path": "embedding",
    "queryVector": [0.1, 0.2, ...],  # 768-dim
    "numCandidates": 100,
    "limit": 10,
    "filter": {
      "category.primary": "Tools",
      "price.current": {"$lte": 200}
    }
  }
}
```

## 🗂️ Product Schema

```javascript
{
  "_id": ObjectId,
  "product_id": "SKU-TOO-00001",
  "name": "DeWalt Cordless Drill Driver Kit",
  "description": "20V MAX lithium-ion cordless drill",
  "long_description": "Professional-grade cordless drill...",
  "category": {
    "primary": "Tools",
    "subcategory": "Power Tools",
    "department": "General"
  },
  "brand": "DeWalt",
  "price": {
    "current": 149.99,
    "original": 199.99,
    "currency": "USD"
  },
  "attributes": {
    "voltage": "20V",
    "battery_type": "Lithium-Ion",
    "chuck_size": "1/2 inch"
  },
  "inventory": {
    "in_stock": true,
    "quantity": 45,
    "warehouse_locations": ["WH-01", "WH-02"]
  },
  "images": ["url1", "url2"],
  "ratings": {
    "average": 4.7,
    "count": 234
  },
  "metadata": {
    "created_at": ISODate,
    "updated_at": ISODate,
    "tags": ["tools", "power tools", "dewalt"]
  },
  "embedding": [0.1, 0.2, ...],  // 768-dim vector
  "embedding_text": "Combined text for embedding"
}
```

## 🎨 Frontend Features

### Modern UI Design
- **Dark Theme**: Premium dark mode with vibrant accents
- **Glassmorphism**: Frosted glass effects on cards
- **Smooth Animations**: Micro-interactions and transitions
- **Responsive**: Mobile-friendly design

### User Experience
- **Three Search Modes**: Semantic, Hybrid, Keyword
- **Real-time Filters**: Category and stock filtering
- **AI Chat Interface**: Conversational product discovery
- **Product Details**: Modal with full specifications
- **Visual Feedback**: Loading states and empty states

## 🧪 Testing

### Run Backend Tests
```bash
pytest backend/tests/ -v
```

### Manual Testing Checklist

1. **Database Connection**
   ```bash
   python scripts/setup_indexes.py
   ```

2. **Product Generation**
   ```bash
   python scripts/generate_products.py
   ```

3. **API Endpoints**
   ```bash
   curl http://localhost:8000/api/products
   ```

4. **Semantic Search**
   ```bash
   curl -X POST http://localhost:8000/api/products/semantic-search \
     -H "Content-Type: application/json" \
     -d '{"query": "outdoor furniture"}'
   ```

5. **AI Agent**
   ```bash
   curl -X POST http://localhost:8000/api/chat \
     -H "Content-Type: application/json" \
     -d '{"message": "Show me power tools under $150"}'
   ```

## 📊 Sample Data

The system includes 500+ realistic products across:

- **Tools** (Power Tools, Hand Tools, Accessories)
- **Electronics** (Computers, Smartphones, Tablets)
- **Furniture** (Living Room, Bedroom, Office, Outdoor)
- **Appliances** (Kitchen, Laundry, Cleaning)
- **Home Improvement** (Paint, Hardware, Lighting, Plumbing)

Each product includes:
- Realistic pricing with occasional discounts
- Detailed descriptions and specifications
- Brand information
- Inventory status
- Customer ratings
- Category-specific attributes

## 🔧 Troubleshooting

### MongoDB Connection Issues
- Verify `MONGODB_URI` in `.env`
- Check IP whitelist in MongoDB Atlas
- Ensure database user has read/write permissions

### VertexAI Errors
- Verify `GOOGLE_APPLICATION_CREDENTIALS` path
- Check service account has VertexAI permissions
- Ensure VertexAI API is enabled in Google Cloud

### Vector Search Not Working
- Confirm Vector Search index is created in Atlas UI
- Index name must be `product_vector_index`
- Wait 5-10 minutes after index creation

### Frontend Not Loading Products
- Check backend is running on port 8000
- Verify CORS is enabled in FastAPI
- Check browser console for errors

## 📝 License

MIT License

## 🤝 Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## 📧 Support

For issues and questions, please open an issue on GitHub.

---

Built with ❤️ using MongoDB Atlas, VertexAI, and FastAPI
