"""VertexAI Agent integration for conversational product search."""
import os
from typing import List, Dict, Any, Optional
from google.cloud import aiplatform
from vertexai.preview import reasoning_engines
from vertexai.generative_models import FunctionDeclaration
import logging

logger = logging.getLogger(__name__)


class ProductCatalogAgent:
    """VertexAI agent for conversational product discovery."""
    
    def __init__(self, vector_search_service):
        self.vector_search = vector_search_service
        self.project_id = os.getenv("GOOGLE_CLOUD_PROJECT")
        self.location = os.getenv("VERTEX_AI_LOCATION", "us-central1")
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
            logger.info("VertexAI Agent initialized")
        except Exception as e:
            logger.error(f"Failed to initialize VertexAI Agent: {e}")
            raise
    
    async def chat(
        self,
        message: str,
        conversation_history: Optional[List[Dict[str, str]]] = None
    ) -> Dict[str, Any]:
        """
        Process a chat message using VertexAI with product catalog tools.
        
        Args:
            message: User message
            conversation_history: Previous conversation messages
        
        Returns:
            Agent response with product recommendations
        """
        if not self._initialized:
            self.initialize()
        
        try:
            from vertexai.generative_models import GenerativeModel, Tool, FunctionDeclaration
            
            # Define tools for the agent
            tools = self._create_agent_tools()
            
            # Create model with tools
            model = GenerativeModel(
                "gemini-1.5-pro",
                tools=[Tool(function_declarations=tools)]
            )
            
            # Build conversation context
            system_instruction = self._get_system_instruction()
            
            # Start chat
            chat = model.start_chat()
            
            # Add conversation history if provided
            if conversation_history:
                for msg in conversation_history:
                    # Note: This is simplified - actual implementation would need proper history handling
                    pass
            
            # Send message and get response
            response = await self._send_message_with_tools(chat, message)
            
            return {
                "response": response["text"],
                "products": response.get("products", []),
                "function_calls": response.get("function_calls", [])
            }
            
        except Exception as e:
            logger.error(f"Agent chat failed: {e}")
            # Fallback to simple search
            return await self._fallback_search(message)
    
    def _create_agent_tools(self) -> List[FunctionDeclaration]:
        """Create function declarations for agent tools."""
        from vertexai.generative_models import FunctionDeclaration
        
        tools = [
            FunctionDeclaration(
                name="search_products",
                description="Search for products using semantic search. Use this when the user asks about finding products.",
                parameters={
                    "type": "object",
                    "properties": {
                        "query": {
                            "type": "string",
                            "description": "Search query describing what the user is looking for"
                        },
                        "limit": {
                            "type": "integer",
                            "description": "Number of products to return (default: 5)",
                            "default": 5
                        }
                    },
                    "required": ["query"]
                }
            ),
            FunctionDeclaration(
                name="filter_by_category",
                description="Filter products by category. Use when user specifies a category.",
                parameters={
                    "type": "object",
                    "properties": {
                        "category": {
                            "type": "string",
                            "description": "Product category (e.g., 'Tools', 'Electronics', 'Furniture')"
                        },
                        "limit": {
                            "type": "integer",
                            "description": "Number of products to return",
                            "default": 5
                        }
                    },
                    "required": ["category"]
                }
            ),
            FunctionDeclaration(
                name="filter_by_price_range",
                description="Find products within a specific price range.",
                parameters={
                    "type": "object",
                    "properties": {
                        "min_price": {
                            "type": "number",
                            "description": "Minimum price"
                        },
                        "max_price": {
                            "type": "number",
                            "description": "Maximum price"
                        },
                        "query": {
                            "type": "string",
                            "description": "Optional search query"
                        }
                    },
                    "required": ["max_price"]
                }
            ),
            FunctionDeclaration(
                name="check_availability",
                description="Check if products are in stock.",
                parameters={
                    "type": "object",
                    "properties": {
                        "query": {
                            "type": "string",
                            "description": "Product search query"
                        }
                    },
                    "required": ["query"]
                }
            )
        ]
        
        return tools
    
    def _get_system_instruction(self) -> str:
        """Get system instruction for the agent."""
        return """You are a helpful product catalog assistant for a retail store. 
        
Your role is to help customers find products they're looking for by:
- Understanding their needs and preferences
- Searching the product catalog using semantic search
- Filtering by category, price, and availability
- Providing detailed product information
- Comparing products when asked
- Making personalized recommendations

Always be friendly, helpful, and concise. When showing products, include:
- Product name and brand
- Price
- Key features
- Availability status

If a product is out of stock, suggest similar alternatives. 
When users ask for comparisons, highlight the key differences.
Ground all responses in actual product data from the catalog."""
    
    async def _send_message_with_tools(
        self,
        chat,
        message: str
    ) -> Dict[str, Any]:
        """Send message and handle tool calls."""
        response = chat.send_message(message)
        
        result = {
            "text": "",
            "products": [],
            "function_calls": []
        }
        
        # Check if response has function calls
        if hasattr(response, 'candidates') and response.candidates:
            candidate = response.candidates[0]
            
            if hasattr(candidate, 'content') and candidate.content.parts:
                for part in candidate.content.parts:
                    # Handle text response
                    if hasattr(part, 'text') and part.text:
                        result["text"] += part.text
                    
                    # Handle function calls
                    if hasattr(part, 'function_call') and part.function_call:
                        func_call = part.function_call
                        func_name = func_call.name
                        func_args = dict(func_call.args)
                        
                        # Execute the function
                        func_result = await self._execute_tool(func_name, func_args)
                        
                        result["function_calls"].append({
                            "name": func_name,
                            "args": func_args,
                            "result": func_result
                        })
                        
                        if func_result.get("products"):
                            result["products"].extend(func_result["products"])
        
        # If no text response, generate one from products
        if not result["text"] and result["products"]:
            result["text"] = self._format_product_response(result["products"])
        
        return result
    
    async def _execute_tool(self, tool_name: str, args: Dict[str, Any]) -> Dict[str, Any]:
        """Execute a tool function."""
        try:
            if tool_name == "search_products":
                products = await self.vector_search.semantic_search(
                    query=args["query"],
                    limit=args.get("limit", 5)
                )
                return {"products": products}
            
            elif tool_name == "filter_by_category":
                products = await self.vector_search.semantic_search(
                    query=args.get("query", args["category"]),
                    limit=args.get("limit", 5),
                    filters={"category": args["category"]}
                )
                return {"products": products}
            
            elif tool_name == "filter_by_price_range":
                filters = {}
                if "min_price" in args:
                    filters["min_price"] = args["min_price"]
                if "max_price" in args:
                    filters["max_price"] = args["max_price"]
                
                products = await self.vector_search.semantic_search(
                    query=args.get("query", ""),
                    limit=args.get("limit", 5),
                    filters=filters
                )
                return {"products": products}
            
            elif tool_name == "check_availability":
                products = await self.vector_search.semantic_search(
                    query=args["query"],
                    limit=5,
                    filters={"in_stock": True}
                )
                return {"products": products}
            
            else:
                return {"error": f"Unknown tool: {tool_name}"}
                
        except Exception as e:
            logger.error(f"Tool execution failed: {e}")
            return {"error": str(e)}
    
    def _format_product_response(self, products: List[Dict[str, Any]]) -> str:
        """Format products into a readable response."""
        if not products:
            return "I couldn't find any products matching your criteria."
        
        response = f"I found {len(products)} product(s) for you:\n\n"
        
        for i, product in enumerate(products, 1):
            response += f"{i}. **{product['name']}** by {product['brand']}\n"
            response += f"   Price: ${product['price']['current']:.2f}\n"
            response += f"   {product['description']}\n"
            
            if product.get('inventory', {}).get('in_stock'):
                response += "   ✓ In Stock\n"
            else:
                response += "   ✗ Out of Stock\n"
            
            response += "\n"
        
        return response
    
    async def _fallback_search(self, message: str) -> Dict[str, Any]:
        """Fallback to simple search if agent fails."""
        try:
            products = await self.vector_search.semantic_search(message, limit=5)
            
            return {
                "response": self._format_product_response(products),
                "products": products,
                "function_calls": []
            }
        except Exception as e:
            logger.error(f"Fallback search failed: {e}")
            return {
                "response": "I'm sorry, I'm having trouble searching the catalog right now. Please try again later.",
                "products": [],
                "function_calls": []
            }
