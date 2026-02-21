"""Entity extraction and intent matching for text-to-SQL conversion"""

import re
from dataclasses import dataclass
from typing import Dict, List, Optional


@dataclass
class Entity:
    """Represents an extracted entity"""

    type: str  # e.g., 'customer_name', 'order_id', 'status'
    value: str
    confidence: float = 1.0


@dataclass
class QueryIntent:
    """Represents the query intent"""

    intent_type: str  # e.g., 'get_order_status', 'find_orders_by_customer'
    entities: List[Entity]
    confidence: float = 1.0


class EntityExtractor:
    """
    Systematic entity extraction and intent matching for order queries.
    Uses pattern matching and rules instead of LLM prompts.
    """

    # Pattern for order IDs (ORD-XXXXX format)
    ORDER_ID_PATTERN = re.compile(r'\b(ORD-\d{5})\b', re.IGNORECASE)

    # Pattern for customer names (capitalized words)
    CUSTOMER_NAME_PATTERN = re.compile(
        r'\b(customer|for|by|of|from)\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)?)\b'
    )

    # Status keywords
    STATUS_KEYWORDS = ['pending', 'processing', 'shipped', 'delivered', 'cancelled']

    # Intent keywords mapping
    INTENT_PATTERNS = {
        'get_order_status': [
            r'(status|track|where|check)\s+(of|for|my|the)?\s*(order|shipment|package)',
            r'(what|when|how).*(order|shipment|package)',
            r'order\s+status',
            r'track\s+(my|the)?\s*order',
        ],
        'find_orders_by_customer': [
            r'(orders|purchases)\s+(for|by|from|of)\s+([A-Z][a-z]+)',
            r'(show|get|find|list)\s+(all|the)?\s*orders\s+(for|by|from|of)',
            r'customer\s+([A-Z][a-z]+).*(orders|purchases)',
        ],
    }

    def extract_entities(self, text: str) -> List[Entity]:
        """
        Extract entities from text using pattern matching

        Args:
            text: Input text from user

        Returns:
            List of extracted entities
        """
        entities = []

        # Extract order IDs
        order_matches = self.ORDER_ID_PATTERN.findall(text)
        for order_id in order_matches:
            entities.append(Entity(type='order_id', value=order_id.upper(), confidence=1.0))

        # Extract customer names
        customer_matches = self.CUSTOMER_NAME_PATTERN.findall(text)
        for _, customer_name in customer_matches:
            entities.append(Entity(type='customer_name', value=customer_name, confidence=0.9))

        # Extract status keywords
        text_lower = text.lower()
        for status in self.STATUS_KEYWORDS:
            if status in text_lower:
                entities.append(Entity(type='status', value=status, confidence=0.8))

        return entities

    def match_intent(self, text: str, entities: List[Entity]) -> Optional[QueryIntent]:
        """
        Match query intent based on patterns and entities

        Args:
            text: Input text from user
            entities: Extracted entities

        Returns:
            QueryIntent or None if no match
        """
        text_lower = text.lower()

        # Check each intent pattern
        for intent_type, patterns in self.INTENT_PATTERNS.items():
            for pattern in patterns:
                if re.search(pattern, text_lower):
                    # Match found - calculate confidence based on entities
                    confidence = self._calculate_confidence(intent_type, entities)
                    return QueryIntent(
                        intent_type=intent_type,
                        entities=entities,
                        confidence=confidence
                    )

        # Default to get_order_status if we have order-related entities
        entity_types = {e.type for e in entities}
        if 'order_id' in entity_types or 'customer_name' in entity_types:
            return QueryIntent(
                intent_type='find_orders_by_customer' if 'customer_name' in entity_types
                           else 'get_order_status',
                entities=entities,
                confidence=0.7
            )

        return None

    def _calculate_confidence(self, intent_type: str, entities: List[Entity]) -> float:
        """Calculate confidence score based on intent and entities"""
        if not entities:
            return 0.5

        # Higher confidence if we have relevant entities for the intent
        entity_types = {e.type for e in entities}

        if intent_type == 'get_order_status':
            if 'order_id' in entity_types:
                return 0.95
            elif 'customer_name' in entity_types:
                return 0.85

        elif intent_type == 'find_orders_by_customer':
            if 'customer_name' in entity_types:
                return 0.9

        return 0.7


class SQLQueryBuilder:
    """
    Builds SQL queries from extracted entities and intents.
    Systematic approach without LLM prompts.
    """

    def build_query(self, query_intent: QueryIntent) -> Dict[str, any]:
        """
        Build SQL query from intent and entities

        Args:
            query_intent: Parsed query intent with entities

        Returns:
            Dictionary with 'query' (SQL string) and 'params' (parameters)
        """
        intent_type = query_intent.intent_type
        entities = {e.type: e.value for e in query_intent.entities}

        if intent_type == 'get_order_status':
            return self._build_order_status_query(entities)
        elif intent_type == 'find_orders_by_customer':
            return self._build_customer_orders_query(entities)
        else:
            raise ValueError(f"Unknown intent type: {intent_type}")

    def _build_order_status_query(self, entities: Dict[str, str]) -> Dict[str, any]:
        """Build query to get order status"""
        if 'order_id' in entities:
            return {
                'query': """
                    SELECT id, customer_name, status, items, total_amount,
                           tracking_number, estimated_delivery, created_at
                    FROM orders
                    WHERE id = :order_id
                """,
                'params': {'order_id': entities['order_id']}
            }
        elif 'customer_name' in entities:
            return {
                'query': """
                    SELECT id, customer_name, status, items, total_amount,
                           tracking_number, estimated_delivery, created_at
                    FROM orders
                    WHERE LOWER(customer_name) = LOWER(:customer_name)
                    ORDER BY created_at DESC
                    LIMIT 5
                """,
                'params': {'customer_name': entities['customer_name']}
            }
        else:
            raise ValueError("Need either order_id or customer_name to query orders")

    def _build_customer_orders_query(self, entities: Dict[str, str]) -> Dict[str, any]:
        """Build query to find all orders for a customer"""
        if 'customer_name' not in entities:
            raise ValueError("Need customer_name to query customer orders")

        query = """
            SELECT id, customer_name, status, items, total_amount,
                   tracking_number, estimated_delivery, created_at
            FROM orders
            WHERE LOWER(customer_name) = LOWER(:customer_name)
            ORDER BY created_at DESC
        """
        params = {'customer_name': entities['customer_name']}

        # Add status filter if specified
        if 'status' in entities:
            query = query.replace('ORDER BY', 'AND status = :status\nORDER BY')
            params['status'] = entities['status']

        return {'query': query, 'params': params}
