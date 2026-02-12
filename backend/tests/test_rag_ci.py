"""Tests for RAG (Retrieval-Augmented Generation) - CI version with mocked API calls"""

from pathlib import Path
from unittest.mock import AsyncMock, Mock, patch

import pytest

from app.agents.rag import RAGAgent
from app.agents.state import ConversationState, Message


@pytest.fixture
def mock_qdrant():
    """Mock Qdrant client"""
    mock_client = Mock()
    mock_client.get_collections.return_value = Mock(collections=[])
    mock_client.create_collection.return_value = None
    mock_client.upsert.return_value = None
    # Create mock search results with score > 0.7
    result1 = Mock()
    result1.payload = {"text": "We offer 24/7 customer support", "source": "support"}
    result1.score = 0.85
    result2 = Mock()
    result2.payload = {"text": "Returns within 30 days", "source": "returns"}
    result2.score = 0.80
    mock_client.search.return_value = [result1, result2]
    return mock_client


@pytest.fixture
def mock_embeddings():
    """Mock Google Gemini embeddings"""
    mock_emb = Mock()
    mock_emb.embed_query = AsyncMock(return_value=[0.1] * 768)  # Gemini embedding size
    return mock_emb


@pytest.fixture
def rag_agent(mock_qdrant, mock_embeddings):
    """Create RAG agent with mocked dependencies"""
    with patch("app.agents.rag.QdrantClient", return_value=mock_qdrant):
        with patch("app.agents.rag.GoogleGenerativeAIEmbeddings", return_value=mock_embeddings):
            with patch("app.agents.rag.ChatGoogleGenerativeAI") as mock_llm_class:
                # Mock the ChatGoogleGenerativeAI instance
                mock_llm = Mock()
                mock_llm_class.return_value = mock_llm

                agent = RAGAgent()
                agent.qdrant = mock_qdrant
                agent.embeddings = mock_embeddings
                agent.llm = mock_llm
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
        assert all(len(chunk) <= 70 for chunk in chunks)  # Some flex for chunking

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
        """Test retrieving relevant documents"""
        query = "How do I get support?"

        results = await rag_agent.retrieve(query, top_k=2)

        assert len(results) <= 2
        assert all(isinstance(doc, str) for doc in results)
        # Mock returns support-related documents
        assert any("support" in doc.lower() for doc in results)

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
    async def test_retrieve_handles_errors(self, rag_agent):
        """Test that retrieve handles errors gracefully"""
        rag_agent.qdrant.search.side_effect = Exception("Search failed")

        results = await rag_agent.retrieve("test query")

        assert results == []


class TestRAGAgent:
    """Test RAG agent end-to-end"""

    @pytest.mark.asyncio
    async def test_rag_agent_with_knowledge_query(self, rag_agent):
        """Test RAG agent processing a knowledge query"""
        # Mock the LLM response
        mock_llm_response = Mock()
        mock_llm_response.content = (
            "Based on our support policy, we offer 24/7 assistance."
        )

        # Create async mock
        async def mock_ainvoke(*args, **kwargs):
            return mock_llm_response

        rag_agent.llm.ainvoke = mock_ainvoke

        state = ConversationState(
            messages=[Message(role="user", content="What support do you offer?")],
            intent="knowledge",
        )

        result = await rag_agent.run(state)

        assert result.response is not None
        assert len(result.retrieved_docs) > 0
        assert result.next_step == "end"

    @pytest.mark.asyncio
    async def test_rag_agent_with_no_relevant_docs(self, rag_agent):
        """Test RAG agent when no relevant documents found"""
        # Mock empty search results
        rag_agent.qdrant.search.return_value = []

        # Mock the LLM response
        mock_llm_response = Mock()
        mock_llm_response.content = "I don't have specific information about that."

        async def mock_ainvoke(*args, **kwargs):
            return mock_llm_response

        rag_agent.llm.ainvoke = mock_ainvoke

        state = ConversationState(
            messages=[Message(role="user", content="Random query")],
            intent="knowledge",
        )

        result = await rag_agent.run(state)

        assert result.response is not None
        assert "don't have specific information" in result.response.lower()

    @pytest.mark.asyncio
    async def test_rag_agent_handles_llm_errors(self, rag_agent):
        """Test RAG agent handles LLM errors gracefully"""
        with patch.object(rag_agent, "llm") as mock_llm:
            mock_llm.ainvoke.side_effect = Exception("LLM failed")

            state = ConversationState(
                messages=[Message(role="user", content="Test query")],
                intent="knowledge",
            )

            result = await rag_agent.run(state)

            assert result.response is not None
            assert (
                "error" in result.response.lower()
                or "sorry" in result.response.lower()
            )


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
                },
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
            )

            assert response.status_code == 200
            data = response.json()

            # Response should have metadata
            assert "metadata" in data
            # Should include docs retrieved info
            assert data["metadata"]["docs_retrieved"] == 3
            assert "timestamp" in data["metadata"]
