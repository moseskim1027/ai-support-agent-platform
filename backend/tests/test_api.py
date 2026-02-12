"""Tests for FastAPI endpoints"""

import uuid
from unittest.mock import patch


def test_health_endpoint(client):
    """Test health check endpoint"""
    response = client.get("/api/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert "timestamp" in data
    assert "version" in data


def test_live_endpoint(client):
    """Test liveness probe endpoint"""
    response = client.get("/api/live")
    assert response.status_code == 200
    assert response.json() == {"status": "alive"}


def test_ready_endpoint(client):
    """Test readiness probe endpoint"""
    response = client.get("/api/ready")
    assert response.status_code == 200
    assert response.json() == {"status": "ready"}


@patch("app.api.chat.orchestrator")
def test_chat_endpoint_success(mock_orchestrator, client):
    """Test chat endpoint with successful response"""

    # Mock orchestrator response
    async def mock_process(*args, **kwargs):
        return {
            "message": "Hello! How can I help you?",
            "intent": "conversation",
            "agent_used": "responder",
            "metadata": {"tool_calls": 0, "docs_retrieved": 0},
        }

    mock_orchestrator.process = mock_process

    response = client.post("/api/chat", json={"message": "Hello!"})

    assert response.status_code == 200
    data = response.json()
    assert data["message"] == "Hello! How can I help you?"
    assert data["intent"] == "conversation"
    assert data["agent_type"] == "responder"
    assert "metadata" in data


@patch("app.api.chat.orchestrator")
def test_chat_endpoint_with_conversation_id(mock_orchestrator, client):
    """Test chat endpoint with conversation ID"""
    test_uuid = str(uuid.uuid4())

    async def mock_process(*args, **kwargs):
        return {
            "message": "Test response",
            "intent": "conversation",
            "agent_used": "responder",
            "metadata": {},
        }

    mock_orchestrator.process = mock_process

    response = client.post("/api/chat", json={"message": "Test", "conversation_id": test_uuid})

    assert response.status_code == 200
    data = response.json()
    assert "conversation_id" in data
    assert data["conversation_id"] == test_uuid


@patch("app.api.chat.orchestrator")
def test_chat_endpoint_knowledge_intent(mock_orchestrator, client):
    """Test chat endpoint with knowledge question"""

    async def mock_process(*args, **kwargs):
        return {
            "message": "Our return policy allows returns within 30 days.",
            "intent": "knowledge",
            "agent_used": "rag",
            "metadata": {"tool_calls": 0, "docs_retrieved": 3},
        }

    mock_orchestrator.process = mock_process

    response = client.post("/api/chat", json={"message": "What is your return policy?"})

    assert response.status_code == 200
    data = response.json()
    assert data["intent"] == "knowledge"
    assert data["agent_type"] == "rag"
    assert data["metadata"]["docs_retrieved"] == 3


@patch("app.api.chat.orchestrator")
def test_chat_endpoint_action_intent(mock_orchestrator, client):
    """Test chat endpoint with action request"""

    async def mock_process(*args, **kwargs):
        return {
            "message": "Your order #12345 has been shipped.",
            "intent": "action",
            "agent_used": "tool",
            "metadata": {"tool_calls": 1, "docs_retrieved": 0},
        }

    mock_orchestrator.process = mock_process

    response = client.post("/api/chat", json={"message": "Check order status for order 12345"})

    assert response.status_code == 200
    data = response.json()
    assert data["intent"] == "action"
    assert data["agent_type"] == "tool"
    assert data["metadata"]["tool_calls"] == 1


def test_chat_endpoint_empty_message(client):
    """Test chat endpoint with empty message"""
    response = client.post("/api/chat", json={"message": ""})
    assert response.status_code == 422  # Validation error


def test_chat_endpoint_missing_message(client):
    """Test chat endpoint with missing message field"""
    response = client.post("/api/chat", json={})
    assert response.status_code == 422  # Validation error


@patch("app.api.chat.orchestrator")
def test_chat_endpoint_error_handling(mock_orchestrator, client):
    """Test chat endpoint handles orchestrator errors"""

    async def mock_process(*args, **kwargs):
        return {
            "message": "I apologize, but I encountered an error processing your request.",
            "intent": "error",
            "agent_used": "none",
            "metadata": {"error": "Test error"},
        }

    mock_orchestrator.process = mock_process

    response = client.post("/api/chat", json={"message": "Test message"})

    assert response.status_code == 200
    data = response.json()
    assert data["intent"] == "error"
    assert data["agent_type"] == "none"
    assert "error" in data["metadata"]


def test_docs_endpoint(client):
    """Test API documentation endpoint is accessible"""
    response = client.get("/api/docs")
    assert response.status_code == 200


def test_openapi_endpoint(client):
    """Test OpenAPI schema endpoint"""
    response = client.get("/openapi.json")
    assert response.status_code == 200
    data = response.json()
    assert "openapi" in data
    assert "info" in data
    assert "paths" in data
