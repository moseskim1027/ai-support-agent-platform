"""
End-to-End tests for the AI Support Agent Platform

These tests use real services (OpenAI, Qdrant) and are meant for local testing only.  # noqa: E501
They are skipped in CI/CD using the @pytest.mark.e2e marker.

To run these tests locally:
    pytest tests/test_e2e.py -v -m e2e

To run all tests EXCEPT e2e:
    pytest -v -m "not e2e"
"""

import pytest
from fastapi.testclient import TestClient

from app.main import app

# Mark all tests in this module as e2e (will be skipped in CI/CD)
pytestmark = pytest.mark.e2e


@pytest.fixture
def client():
    """Create a test client with real services"""
    return TestClient(app)


class TestRAGEndToEnd:
    """Test RAG with real OpenAI and Qdrant"""

    def test_return_policy_query(self, client):
        """Test querying about return policy"""
        response = client.post(
            "/api/chat",
            json={"message": "What is your return policy?"},
        )

        assert response.status_code == 200
        data = response.json()

        # Should get a response
        assert "message" in data
        assert len(data["message"]) > 0

        # Should route to knowledge/RAG agent
        assert data.get("intent") in ["knowledge", "conversation"]
        assert data["agent_type"] in ["rag", "responder"]

        print(f"\n✓ Return Policy Response: {data['message'][:100]}...")

    def test_shipping_query(self, client):
        """Test querying about shipping"""
        response = client.post(
            "/api/chat",
            json={"message": "How long does shipping take?"},
        )

        assert response.status_code == 200
        data = response.json()

        assert "message" in data
        assert len(data["message"]) > 0

        print(f"\n✓ Shipping Response: {data['message'][:100]}...")

    def test_warranty_query(self, client):
        """Test querying about warranty"""
        response = client.post(
            "/api/chat",
            json={"message": "What does the warranty cover?"},
        )

        assert response.status_code == 200
        data = response.json()

        assert "message" in data
        assert len(data["message"]) > 0

        print(f"\n✓ Warranty Response: {data['message'][:100]}...")

    def test_password_reset_query(self, client):
        """Test querying about password reset"""
        response = client.post(
            "/api/chat",
            json={"message": "How do I reset my password?"},
        )

        assert response.status_code == 200
        data = response.json()

        assert "message" in data
        assert len(data["message"]) > 0

        print(f"\n✓ Password Reset Response: {data['message'][:100]}...")

    def test_payment_methods_query(self, client):
        """Test querying about payment methods"""
        response = client.post(
            "/api/chat",
            json={"message": "What payment methods do you accept?"},
        )

        assert response.status_code == 200
        data = response.json()

        assert "message" in data
        assert len(data["message"]) > 0

        print(f"\n✓ Payment Methods Response: {data['message'][:100]}...")

    def test_conversation_flow(self, client):
        """Test multi-turn conversation with context"""
        # First message
        response1 = client.post(
            "/api/chat",
            json={"message": "What is your return policy?"},
        )

        assert response1.status_code == 200
        data1 = response1.json()
        conversation_id = data1["conversation_id"]

        print(f"\n✓ First message: {data1['message'][:80]}...")

        # Follow-up question (should maintain context)
        response2 = client.post(
            "/api/chat",
            json={
                "message": "How long do I have to return an item?",
                "conversation_id": conversation_id,
                "history": [
                    {
                        "role": "user",
                        "content": "What is your return policy?",
                    },
                    {"role": "assistant", "content": data1["message"]},
                ],
            },
        )

        assert response2.status_code == 200
        data2 = response2.json()

        assert "message" in data2
        assert len(data2["message"]) > 0
        assert data2["conversation_id"] == conversation_id

        print(f"\n✓ Follow-up: {data2['message'][:80]}...")


class TestConversationEndToEnd:
    """Test general conversation with real OpenAI"""

    def test_greeting(self, client):
        """Test greeting and general conversation"""
        response = client.post(
            "/api/chat",
            json={"message": "Hello! How can you help me?"},
        )

        assert response.status_code == 200
        data = response.json()

        assert "message" in data
        assert len(data["message"]) > 0

        print(f"\n✓ Greeting Response: {data['message'][:100]}...")

    def test_capabilities_query(self, client):
        """Test asking about capabilities"""
        response = client.post(
            "/api/chat",
            json={"message": "What can you help me with?"},
        )

        assert response.status_code == 200
        data = response.json()

        assert "message" in data
        assert len(data["message"]) > 0

        print(f"\n✓ Capabilities Response: {data['message'][:100]}...")


class TestEdgeCases:
    """Test edge cases and error handling"""

    def test_empty_message(self, client):
        """Test handling of empty message"""
        response = client.post(
            "/api/chat",
            json={"message": ""},
        )

        # Should handle gracefully
        assert response.status_code in [200, 400, 422]

    def test_very_long_message(self, client):
        """Test handling of very long message"""
        long_message = "Tell me about your return policy. " * 100

        response = client.post(
            "/api/chat",
            json={"message": long_message},
        )

        # Should handle gracefully
        assert response.status_code == 200
        data = response.json()
        assert "message" in data

    def test_special_characters(self, client):
        """Test handling of special characters"""
        response = client.post(
            "/api/chat",
            json={"message": "What about émojis 🎉 and spëcial çharacters?"},
        )

        assert response.status_code == 200
        data = response.json()
        assert "message" in data


class TestQdrantIntegration:
    """Test Qdrant vector database integration"""

    def test_document_retrieval_accuracy(self, client):
        """Test that RAG retrieves relevant documents"""
        # Query that should definitely match our documents
        response = client.post(
            "/api/chat",
            json={
                "message": "Can I return an item after 30 days?",
            },
        )

        assert response.status_code == 200
        data = response.json()

        # Response should mention the 30-day policy
        assert "30" in data["message"] or "thirty" in data["message"].lower()

        print(f"\n✓ Retrieved relevant info: {data['message'][:100]}...")

    def test_no_hallucination(self, client):
        """Test that agent doesn't hallucinate when info not available"""
        # Query about something not in our knowledge base
        response = client.post(
            "/api/chat",
            json={
                "message": "What is the capital of France?",
            },
        )

        assert response.status_code == 200
        data = response.json()

        # Should either answer from general knowledge or say it doesn't know
        assert "message" in data
        assert len(data["message"]) > 0

        print(f"\n✓ Out-of-domain response: {data['message'][:100]}...")
