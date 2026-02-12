"""Tests for agent orchestration - CI version with mocked API calls"""

from unittest.mock import AsyncMock, Mock, patch

import pytest

from app.agents.router import RouterAgent
from app.agents.state import ConversationState, Message


@pytest.mark.asyncio
async def test_router_agent_knowledge_intent():
    """Test router classifies knowledge questions correctly"""
    with patch("app.agents.router.ChatGoogleGenerativeAI") as mock_llm_class:
        # Mock the LLM response
        mock_llm = Mock()
        mock_response = Mock()
        mock_response.content = "knowledge|This is a question about company policies"
        mock_llm.ainvoke = AsyncMock(return_value=mock_response)
        mock_llm_class.return_value = mock_llm

        router = RouterAgent()

        state = ConversationState(
            messages=[Message(role="user", content="What is your return policy?")]
        )

        result = await router.run(state)

        assert result.intent == "knowledge"
        assert result.next_step == "rag"


@pytest.mark.asyncio
async def test_router_agent_action_intent():
    """Test router classifies action requests correctly"""
    with patch("app.agents.router.ChatGoogleGenerativeAI") as mock_llm_class:
        # Mock the LLM response
        mock_llm = Mock()
        mock_response = Mock()
        mock_response.content = "action|User wants to check order status"
        mock_llm.ainvoke = AsyncMock(return_value=mock_response)
        mock_llm_class.return_value = mock_llm

        router = RouterAgent()

        state = ConversationState(
            messages=[Message(role="user", content="Check my order status for order 12345")]
        )

        result = await router.run(state)

        assert result.intent == "action"
        assert result.next_step == "tool"


@pytest.mark.asyncio
async def test_router_agent_conversation_intent():
    """Test router classifies greetings correctly"""
    with patch("app.agents.router.ChatGoogleGenerativeAI") as mock_llm_class:
        # Mock the LLM response
        mock_llm = Mock()
        mock_response = Mock()
        mock_response.content = "conversation|This is a greeting"
        mock_llm.ainvoke = AsyncMock(return_value=mock_response)
        mock_llm_class.return_value = mock_llm

        router = RouterAgent()

        state = ConversationState(messages=[Message(role="user", content="Hello!")])

        result = await router.run(state)

        assert result.intent == "conversation"
        assert result.next_step == "respond"


@pytest.mark.asyncio
async def test_router_agent_handles_llm_errors():
    """Test router handles LLM errors gracefully"""
    with patch("app.agents.router.ChatGoogleGenerativeAI") as mock_llm_class:
        # Mock LLM to raise an exception
        mock_llm = Mock()
        mock_llm.ainvoke = AsyncMock(side_effect=Exception("API Error"))
        mock_llm_class.return_value = mock_llm

        router = RouterAgent()

        state = ConversationState(
            messages=[Message(role="user", content="Test message")]
        )

        result = await router.run(state)

        # Should default to conversation on error
        assert result.intent == "conversation"
        assert result.next_step == "respond"


@pytest.mark.asyncio
async def test_router_agent_invalid_intent_response():
    """Test router handles invalid intent responses"""
    with patch("app.agents.router.ChatGoogleGenerativeAI") as mock_llm_class:
        # Mock the LLM to return invalid intent
        mock_llm = Mock()
        mock_response = Mock()
        mock_response.content = "invalid_intent|Some reasoning"
        mock_llm.ainvoke = AsyncMock(return_value=mock_response)
        mock_llm_class.return_value = mock_llm

        router = RouterAgent()

        state = ConversationState(
            messages=[Message(role="user", content="Test message")]
        )

        result = await router.run(state)

        # Should default to conversation for invalid intent
        assert result.intent == "conversation"
        assert result.next_step == "respond"
