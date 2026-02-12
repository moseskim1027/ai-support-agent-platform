"""Tests for RAG (Retrieval-Augmented Generation) functionality - Local testing with real API"""

from unittest.mock import patch

import pytest

from app.agents.rag import RAGAgent
from app.agents.state import ConversationState, Message


@pytest.fixture
def rag_agent():
    """Create RAG agent with real Gemini API - for local testing only"""
    # This will use real Gemini API calls for local development testing
    # For CI, use test_rag_ci.py which has mocked dependencies
    agent = RAGAgent()
    return agent


class TestRAGTextChunking:
    """Test text chunking functionality"""

    def test_chunk_short_text(self, rag_agent):
        """Test chunking of short text"""
        text = "This is a short text that doesn't need chunking."
        chunks = rag_agent._chunk_text(text, max_length=500)

        assert len(chunks) == 1
        assert chunks[0] == text

    def test_chunk_long_text_by_paragraphs(self, rag_agent):
        """Test chunking of long text with paragraphs"""
        text = """This is paragraph one.

This is paragraph two.

This is paragraph three."""
        chunks = rag_agent._chunk_text(text, max_length=50)

        assert len(chunks) >= 2
        assert all(len(chunk) <= 70 for chunk in chunks)  # Some flex for chunking  # noqa: E501

    def test_chunk_very_long_paragraph(self, rag_agent):
        """Test chunking of very long paragraph"""
        text = "This is a very long sentence. " * 50
        chunks = rag_agent._chunk_text(text, max_length=100)

        assert len(chunks) > 1
        assert all(chunk.strip() for chunk in chunks)  # No empty chunks

    def test_chunk_preserves_content(self, rag_agent):
        """Test that chunking preserves all content"""
        text = "First paragraph.\n\nSecond paragraph.\n\nThird paragraph."
        chunks = rag_agent._chunk_text(text, max_length=30)

        # Join chunks and remove extra whitespace for comparison
        joined = " ".join(chunks).replace("\n\n", " ")

        assert "First paragraph" in joined
        assert "Second paragraph" in joined
        assert "Third paragraph" in joined


class TestRAGDocumentLoading:
    """Test document loading from files"""

    def test_chunk_text_integration(self, rag_agent):
        """Test that text chunking works with document loading logic"""
        # Test the chunking method directly
        long_text = "First section. " * 50 + "\n\n" + "Second section. " * 50
        chunks = rag_agent._chunk_text(long_text, max_length=100)

        # Should split into multiple chunks
        assert len(chunks) > 1
        # All chunks should be reasonable size
        assert all(len(chunk) <= 150 for chunk in chunks)  # Allow some overage

    def test_embeddings_initialization(self, rag_agent):
        """Test that embeddings component initializes correctly"""
        # Verify embeddings are set up
        assert rag_agent.embeddings is not None

    def test_agent_initialization(self, rag_agent):
        """Test that RAG agent initializes correctly with all components"""
        assert rag_agent.qdrant is not None
        assert rag_agent.embeddings is not None
        assert rag_agent.llm is not None
        assert rag_agent.collection_name == "knowledge_base"
        assert rag_agent.prompt is not None


class TestRAGRetrieval:
    """Test RAG retrieval functionality"""

    @pytest.mark.asyncio
    async def test_retrieve_relevant_documents(self, rag_agent):
        """Test retrieving relevant documents with real API"""
        query = "How do I get support?"

        results = await rag_agent.retrieve(query, top_k=2)

        # Results should be list of strings
        assert isinstance(results, list)
        assert len(results) <= 2
        assert all(isinstance(doc, str) for doc in results)

    @pytest.mark.asyncio
    async def test_retrieve_with_no_qdrant(self):
        """Test retrieval when Qdrant is not available"""
        with patch("app.agents.rag.QdrantClient", side_effect=Exception("Connection failed")):
            with patch("app.agents.rag.GoogleGenerativeAIEmbeddings"):
                with patch("app.agents.rag.ChatGoogleGenerativeAI"):
                    agent = RAGAgent()
                    agent.qdrant = None

                    results = await agent.retrieve("test query")

                    assert results == []

    @pytest.mark.asyncio
    async def test_retrieve_returns_list(self, rag_agent):
        """Test that retrieve returns a list"""
        results = await rag_agent.retrieve("test query", top_k=1)

        # Should return a list (may be empty)
        assert isinstance(results, list)


class TestRAGAgent:
    """Test RAG agent end-to-end with real Gemini API"""

    @pytest.mark.asyncio
    async def test_rag_agent_with_knowledge_query(self, rag_agent):
        """Test RAG agent processing a knowledge query with real API"""
        state = ConversationState(
            messages=[Message(role="user", content="What support do you offer?")],
            intent="knowledge",
        )

        result = await rag_agent.run(state)

        # Verify response structure (content will vary based on real API)
        assert result.response is not None
        assert isinstance(result.response, str)
        assert result.next_step == "end"

    @pytest.mark.asyncio
    async def test_rag_agent_basic_query(self, rag_agent):
        """Test RAG agent with a simple query using real API"""
        state = ConversationState(
            messages=[Message(role="user", content="Hello, can you help me?")],
            intent="knowledge",
        )

        result = await rag_agent.run(state)

        # Verify basic response structure
        assert result.response is not None
        assert isinstance(result.response, str)
        assert len(result.response) > 0


class TestRAGIntegration:
    """Integration tests for RAG with chat API"""

    def test_chat_api_with_knowledge_intent(self, client):
        """Test chat API routes to RAG for knowledge queries"""
        # Mock the orchestrator at the module level before it gets imported
        with patch("app.api.chat.orchestrator") as mock_orchestrator:
            # Create async mock for process method
            async def mock_process(*args, **kwargs):
                return {
                    "message": "You can return items within 30 days.",
                    "agent_used": "rag",
                    "intent": "knowledge",
                    "metadata": {"docs_retrieved": 2},
                }

            mock_orchestrator.process = mock_process

            response = client.post(
                "/api/chat",
                json={
                    "message": "What is your return policy?",
                    "conversation_id": "test-123",
                },  # noqa: E501
            )

            assert response.status_code == 200
            data = response.json()

            # Should have correct structure
            assert data["intent"] == "knowledge"
            assert "message" in data
            assert data["conversation_id"] == "test-123"
            assert data["agent_type"] == "rag"

    def test_rag_response_includes_metadata(self, client):
        """Test that RAG responses include metadata"""
        # Mock the orchestrator
        with patch("app.api.chat.orchestrator") as mock_orchestrator:
            # Create async mock
            async def mock_process(*args, **kwargs):
                return {
                    "message": "We offer standard and express shipping.",
                    "agent_used": "rag",
                    "intent": "knowledge",
                    "metadata": {"docs_retrieved": 3, "agent": "rag"},
                }

            mock_orchestrator.process = mock_process

            response = client.post(
                "/api/chat", json={"message": "Tell me about shipping options"}
            )  # noqa: E501

            assert response.status_code == 200
            data = response.json()

            # Response should have metadata
            assert "metadata" in data
            # Should include docs retrieved info
            assert data["metadata"]["docs_retrieved"] == 3
            assert "timestamp" in data["metadata"]
