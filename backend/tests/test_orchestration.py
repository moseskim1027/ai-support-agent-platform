"""Integration tests for agent orchestration workflow"""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.orchestration.workflow import AgentOrchestrator


@pytest.mark.asyncio
async def test_orchestrator_initialization():
    """Test orchestrator initializes correctly"""
    with patch.object(AgentOrchestrator, "_build_workflow") as mock_build:
        mock_workflow = MagicMock()
        mock_build.return_value = mock_workflow

        orchestrator = AgentOrchestrator()

        assert orchestrator.router is not None
        assert orchestrator.rag_agent is not None
        assert orchestrator.tool_agent is not None
        assert orchestrator.responder is not None
        assert orchestrator.workflow is not None


@pytest.mark.asyncio
async def test_orchestrator_knowledge_flow():
    """Test complete workflow for knowledge questions"""
    with patch.object(AgentOrchestrator, "_build_workflow") as mock_build:
        # Return dict (not MagicMock) - LangGraph works with dicts
        mock_state = {
            "response": "Our return policy allows returns within 30 days.",
            "intent": "knowledge",
            "current_agent": "rag",
            "messages": [{"role": "user", "content": "What is your return policy?"}],  # noqa: E501
            "tool_calls": [],
            "retrieved_docs": ["doc1"],
            "metadata": {},
        }

        mock_workflow = MagicMock()
        mock_workflow.ainvoke = AsyncMock(return_value=mock_state)
        mock_build.return_value = mock_workflow

        orchestrator = AgentOrchestrator()
        result = await orchestrator.process("What is your return policy?")

        assert "message" in result
        assert isinstance(result["message"], str)


@pytest.mark.asyncio
async def test_orchestrator_action_flow():
    """Test complete workflow for action requests"""
    with patch.object(AgentOrchestrator, "_build_workflow") as mock_build:
        # Return dict (not MagicMock) - LangGraph works with dicts
        mock_state = {
            "response": "Your order has been shipped.",
            "intent": "action",
            "current_agent": "tool",
            "messages": [{"role": "user", "content": "Check order 12345"}],
            "tool_calls": [{"tool": "get_order_status"}],
            "retrieved_docs": [],
            "metadata": {},
        }

        mock_workflow = MagicMock()
        mock_workflow.ainvoke = AsyncMock(return_value=mock_state)
        mock_build.return_value = mock_workflow

        orchestrator = AgentOrchestrator()
        result = await orchestrator.process("Check order 12345")

        assert "message" in result
        assert isinstance(result["message"], str)


@pytest.mark.asyncio
async def test_orchestrator_conversation_flow():
    """Test complete workflow for conversation"""
    with patch.object(AgentOrchestrator, "_build_workflow") as mock_build:
        # Return dict (not MagicMock) - LangGraph works with dicts
        mock_state = {
            "response": "Hello! How can I help you?",
            "intent": "conversation",
            "current_agent": "responder",
            "messages": [{"role": "user", "content": "Hello!"}],
            "tool_calls": [],
            "retrieved_docs": [],
            "metadata": {},
        }

        mock_workflow = MagicMock()
        mock_workflow.ainvoke = AsyncMock(return_value=mock_state)
        mock_build.return_value = mock_workflow

        orchestrator = AgentOrchestrator()
        result = await orchestrator.process("Hello!")

        assert "message" in result
        assert isinstance(result["message"], str)


@pytest.mark.asyncio
async def test_orchestrator_error_handling():
    """Test orchestrator handles errors gracefully"""
    with patch.object(AgentOrchestrator, "_build_workflow") as mock_build:
        mock_workflow = MagicMock()
        mock_workflow.ainvoke = AsyncMock(side_effect=Exception("Test error"))
        mock_build.return_value = mock_workflow

        orchestrator = AgentOrchestrator()
        result = await orchestrator.process("Test message")

        assert result["intent"] == "error"
        assert result["agent_used"] == "none"
        assert "error" in result["message"].lower()
