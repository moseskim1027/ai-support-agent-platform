"""Tests for agent orchestration"""

import pytest

from app.agents.router import RouterAgent
from app.agents.state import ConversationState, Message


@pytest.mark.asyncio
async def test_router_agent_knowledge_intent():
    """Test router classifies knowledge questions correctly"""
    router = RouterAgent()

    state = ConversationState(
        messages=[Message(role="user", content="What is your return policy?")]
    )

    result = await router.run(state)

    assert result.intent in ["knowledge", "conversation"]
    assert result.next_step in ["rag", "respond"]


@pytest.mark.asyncio
async def test_router_agent_action_intent():
    """Test router classifies action requests correctly"""
    router = RouterAgent()

    state = ConversationState(
        messages=[Message(role="user", content="Check my order status for order 12345")]
    )

    result = await router.run(state)

    assert result.intent in ["action", "conversation"]
    assert result.next_step in ["tool", "respond"]


@pytest.mark.asyncio
async def test_router_agent_conversation_intent():
    """Test router classifies greetings correctly"""
    router = RouterAgent()

    state = ConversationState(messages=[Message(role="user", content="Hello!")])

    result = await router.run(state)

    assert result.intent == "conversation"
    assert result.next_step == "respond"
