"""Sample tools for demonstration"""

import random
from datetime import datetime, timedelta
from typing import Any, Dict


def get_order_status(order_id: str) -> Dict[str, Any]:
    """
    Get order status by order ID

    Args:
        order_id: Order ID to lookup

    Returns:
        Order status information
    """
    # Simulated order data
    statuses = ["processing", "shipped", "delivered", "pending"]
    status = random.choice(statuses)

    return {
        "order_id": order_id,
        "status": status,
        "estimated_delivery": (datetime.now() + timedelta(days=random.randint(1, 7))).strftime(
            "%Y-%m-%d"
        ),
        "tracking_number": f"TRK{random.randint(100000, 999999)}",
        "items": random.randint(1, 5),
    }


def cancel_subscription(subscription_id: str, reason: str = "") -> Dict[str, Any]:
    """
    Cancel a subscription

    Args:
        subscription_id: Subscription ID to cancel
        reason: Cancellation reason (optional)

    Returns:
        Cancellation confirmation
    """
    return {
        "success": True,
        "subscription_id": subscription_id,
        "cancelled_at": datetime.now().isoformat(),
        "refund_amount": round(random.uniform(10, 100), 2),
        "message": (
            "Subscription cancelled successfully. "
            "Refund will be processed in 3-5 business days."
        ),
    }


def update_shipping_address(
    order_id: str, address: str, city: str, zip_code: str
) -> Dict[str, Any]:
    """
    Update shipping address for an order

    Args:
        order_id: Order ID
        address: Street address
        city: City
        zip_code: ZIP code

    Returns:
        Update confirmation
    """
    return {
        "success": True,
        "order_id": order_id,
        "new_address": {
            "street": address,
            "city": city,
            "zip_code": zip_code,
            "updated_at": datetime.now().isoformat(),
        },
        "message": "Shipping address updated successfully.",
    }


def get_account_balance(user_id: str) -> Dict[str, Any]:
    """
    Get account balance for a user

    Args:
        user_id: User ID

    Returns:
        Account balance information
    """
    return {
        "user_id": user_id,
        "balance": round(random.uniform(0, 1000), 2),
        "currency": "USD",
        "last_transaction": (datetime.now() - timedelta(days=random.randint(1, 30))).strftime(
            "%Y-%m-%d"
        ),
        "account_status": "active",
    }


def get_sample_tools():
    """Get all sample tools with their schemas"""
    return [
        {
            "name": "get_order_status",
            "func": get_order_status,
            "description": "Get the status of an order by order ID",
            "parameters": {
                "type": "object",
                "properties": {
                    "order_id": {
                        "type": "string",
                        "description": "The order ID to lookup",
                    }
                },
                "required": ["order_id"],
            },
        },
        {
            "name": "cancel_subscription",
            "func": cancel_subscription,
            "description": "Cancel a subscription",
            "parameters": {
                "type": "object",
                "properties": {
                    "subscription_id": {
                        "type": "string",
                        "description": "The subscription ID to cancel",
                    },
                    "reason": {
                        "type": "string",
                        "description": "Optional reason for cancellation",
                    },
                },
                "required": ["subscription_id"],
            },
        },
        {
            "name": "update_shipping_address",
            "func": update_shipping_address,
            "description": "Update the shipping address for an order",
            "parameters": {
                "type": "object",
                "properties": {
                    "order_id": {"type": "string", "description": "Order ID"},
                    "address": {"type": "string", "description": "Street address"},
                    "city": {"type": "string", "description": "City"},
                    "zip_code": {"type": "string", "description": "ZIP code"},
                },
                "required": ["order_id", "address", "city", "zip_code"],
            },
        },
        {
            "name": "get_account_balance",
            "func": get_account_balance,
            "description": "Get account balance for a user",
            "parameters": {
                "type": "object",
                "properties": {
                    "user_id": {
                        "type": "string",
                        "description": "User ID to lookup",
                    }
                },
                "required": ["user_id"],
            },
        },
    ]
