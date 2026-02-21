"""Production-ready tools for the AI support agent"""

from datetime import datetime
from typing import Any, Dict, List

import httpx
from sqlalchemy import text

from app.database.session import AsyncSessionLocal
from app.tools.entity_extractor import EntityExtractor, SQLQueryBuilder


class OrderStatusTool:
    """
    Tool for retrieving order status from database.
    Uses systematic entity extraction and text-to-SQL conversion.
    """

    def __init__(self):
        self.entity_extractor = EntityExtractor()
        self.query_builder = SQLQueryBuilder()

    async def execute(self, query: str) -> Dict[str, Any]:
        """
        Execute order status query using natural language input

        Args:
            query: Natural language query (e.g., "What's the status of order ORD-10001?"
                   or "Show me orders for John Smith")

        Returns:
            Order status information
        """
        # Extract entities from the query
        entities = self.entity_extractor.extract_entities(query)

        if not entities:
            return {
                "success": False,
                "error": "Could not identify order ID or customer name in query. "
                        "Please provide an order ID (e.g., ORD-10001) or customer name."
            }

        # Match intent
        query_intent = self.entity_extractor.match_intent(query, entities)

        if not query_intent:
            return {
                "success": False,
                "error": "Could not understand the query intent. "
                        "Please ask about order status or customer orders."
            }

        # Build SQL query
        try:
            sql_query_data = self.query_builder.build_query(query_intent)
        except ValueError as e:
            return {
                "success": False,
                "error": str(e)
            }

        # Execute query against database
        async with AsyncSessionLocal() as session:
            try:
                result = await session.execute(
                    text(sql_query_data['query']),
                    sql_query_data['params']
                )
                rows = result.fetchall()

                if not rows:
                    entity_info = ", ".join([f"{e.type}={e.value}" for e in entities])
                    return {
                        "success": False,
                        "error": f"No orders found for {entity_info}"
                    }

                # Format results
                orders = []
                for row in rows:
                    orders.append({
                        "order_id": row[0],
                        "customer_name": row[1],
                        "status": row[2],
                        "items": row[3],
                        "total_amount": float(row[4]),
                        "tracking_number": row[5],
                        "estimated_delivery": row[6].isoformat() if row[6] else None,
                        "created_at": row[7].isoformat(),
                    })

                return {
                    "success": True,
                    "query": query,
                    "entities_found": [{"type": e.type, "value": e.value} for e in entities],
                    "intent": query_intent.intent_type,
                    "orders": orders,
                    "count": len(orders)
                }
            finally:
                await session.close()


class WebSearchTool:
    """
    Tool for web search using DuckDuckGo Instant Answer API.
    Provides quick answers and search results.
    """

    DUCKDUCKGO_API = "https://api.duckduckgo.com/"

    async def execute(self, query: str, max_results: int = 5) -> Dict[str, Any]:
        """
        Execute web search query

        Args:
            query: Search query
            max_results: Maximum number of results to return (default: 5)

        Returns:
            Search results with snippets and URLs
        """
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                # DuckDuckGo Instant Answer API
                response = await client.get(
                    self.DUCKDUCKGO_API,
                    params={
                        "q": query,
                        "format": "json",
                        "no_html": 1,
                        "skip_disambig": 1,
                    }
                )
                response.raise_for_status()
                data = response.json()

                # Parse results
                results = []

                # Abstract (main answer)
                if data.get("Abstract"):
                    results.append({
                        "title": data.get("Heading", "Main Result"),
                        "snippet": data["Abstract"],
                        "url": data.get("AbstractURL", ""),
                        "source": data.get("AbstractSource", "DuckDuckGo"),
                        "type": "abstract"
                    })

                # Related topics
                for topic in data.get("RelatedTopics", [])[:max_results]:
                    if isinstance(topic, dict) and "Text" in topic:
                        results.append({
                            "title": topic.get("Text", "")[:100],
                            "snippet": topic.get("Text", ""),
                            "url": topic.get("FirstURL", ""),
                            "source": "DuckDuckGo",
                            "type": "related"
                        })

                # Definition (for word definitions)
                if data.get("Definition"):
                    results.insert(0, {
                        "title": f"Definition: {data.get('Heading', query)}",
                        "snippet": data["Definition"],
                        "url": data.get("DefinitionURL", ""),
                        "source": data.get("DefinitionSource", "DuckDuckGo"),
                        "type": "definition"
                    })

                if not results:
                    return {
                        "success": True,
                        "query": query,
                        "results": [],
                        "count": 0,
                        "message": "No instant results found. Try a more specific query."
                    }

                return {
                    "success": True,
                    "query": query,
                    "results": results[:max_results],
                    "count": len(results[:max_results]),
                    "timestamp": datetime.now().isoformat()
                }

        except httpx.HTTPError as e:
            return {
                "success": False,
                "error": f"Search request failed: {str(e)}"
            }
        except Exception as e:
            return {
                "success": False,
                "error": f"An error occurred during search: {str(e)}"
            }


def get_production_tools() -> List[Dict[str, Any]]:
    """Get production-ready tools with their schemas"""
    order_tool = OrderStatusTool()
    search_tool = WebSearchTool()

    return [
        {
            "name": "get_order_status",
            "func": order_tool.execute,
            "description": (
                "Get order status and tracking information. "
                "Can query by order ID (e.g., ORD-10001) or customer name (e.g., John Smith). "
                "Returns order details including status, items, total, tracking number, and delivery date."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": (
                            "Natural language query about orders. "
                            "Examples: 'What is the status of order ORD-10001?', "
                            "'Show me all orders for John Smith', "
                            "'Track my order'"
                        ),
                    }
                },
                "required": ["query"],
            },
        },
        {
            "name": "web_search",
            "func": search_tool.execute,
            "description": (
                "Search the web for information using DuckDuckGo. "
                "Returns relevant results with snippets and URLs. "
                "Use this for general knowledge questions, current events, or product information."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "The search query",
                    },
                    "max_results": {
                        "type": "integer",
                        "description": "Maximum number of results to return (default: 5)",
                        "default": 5,
                    },
                },
                "required": ["query"],
            },
        },
    ]
