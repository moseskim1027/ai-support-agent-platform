"""Test script for production tools"""

import asyncio
import sys

from app.tools.tools import OrderStatusTool, WebSearchTool


async def test_order_status_tool():
    """Test the order status tool with various queries"""
    print("=" * 70)
    print("TESTING ORDER STATUS TOOL")
    print("=" * 70)

    tool = OrderStatusTool()

    test_cases = [
        "What is the status of order ORD-10001?",
        "Show me orders for John Smith",
        "Track order ORD-10003",
        "Find orders for Jane Doe",
        "What's the status of customer Bob Johnson's order?",
        "Invalid query without order info",
    ]

    for i, query in enumerate(test_cases, 1):
        print(f"\n{i}. Query: {query}")
        print("-" * 70)
        result = await tool.execute(query)

        if result.get("success"):
            print(f"✓ Success!")
            print(f"  Intent: {result.get('intent')}")
            print(f"  Entities: {result.get('entities_found')}")
            print(f"  Orders found: {result.get('count')}")

            for order in result.get("orders", []):
                print(f"\n  Order {order['order_id']}:")
                print(f"    Customer: {order['customer_name']}")
                print(f"    Status: {order['status']}")
                print(f"    Items: {order['items']}")
                print(f"    Total: ${order['total_amount']}")
                print(f"    Tracking: {order['tracking_number'] or 'N/A'}")
                print(f"    Delivery: {order['estimated_delivery'] or 'N/A'}")
        else:
            print(f"✗ Error: {result.get('error')}")


async def test_web_search_tool():
    """Test the web search tool"""
    print("\n\n" + "=" * 70)
    print("TESTING WEB SEARCH TOOL")
    print("=" * 70)

    tool = WebSearchTool()

    test_queries = [
        "What is Python programming language?",
        "FastAPI framework",
        "Docker containers",
    ]

    for i, query in enumerate(test_queries, 1):
        print(f"\n{i}. Query: {query}")
        print("-" * 70)
        result = await tool.execute(query, max_results=3)

        if result.get("success"):
            print(f"✓ Success!")
            print(f"  Results found: {result.get('count')}")

            for j, res in enumerate(result.get("results", []), 1):
                print(f"\n  Result {j}:")
                print(f"    Title: {res.get('title', 'N/A')[:80]}")
                print(f"    Snippet: {res.get('snippet', 'N/A')[:150]}...")
                print(f"    URL: {res.get('url', 'N/A')}")
                print(f"    Type: {res.get('type', 'N/A')}")
        else:
            print(f"✗ Error: {result.get('error')}")


async def main():
    """Run all tests"""
    try:
        await test_order_status_tool()
        await test_web_search_tool()

        print("\n" + "=" * 70)
        print("ALL TESTS COMPLETED")
        print("=" * 70)

    except Exception as e:
        print(f"\n✗ Test failed with error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
