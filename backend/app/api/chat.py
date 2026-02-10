"""Chat API endpoints"""

import logging
import uuid
from datetime import datetime
from typing import List, Optional

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from app.agents.state import Message as AgentMessage
from app.orchestration import AgentOrchestrator

router = APIRouter()
logger = logging.getLogger(__name__)

# Initialize orchestrator (singleton)
orchestrator = AgentOrchestrator()


class Message(BaseModel):
    """Chat message model"""

    role: str = Field(..., description="Message role: user, assistant, or system")
    content: str = Field(..., description="Message content")
    timestamp: Optional[datetime] = None


class ChatRequest(BaseModel):
    """Chat request model"""

    message: str = Field(..., min_length=1, description="User message")
    conversation_id: Optional[str] = Field(None, description="Conversation ID for context")
    history: Optional[List[Message]] = Field(
        default_factory=list, description="Conversation history"
    )


class ChatResponse(BaseModel):
    """Chat response model"""

    message: str = Field(..., description="Agent response")
    conversation_id: str = Field(..., description="Conversation ID")
    agent_type: str = Field(..., description="Type of agent that handled the request")
    intent: Optional[str] = Field(None, description="Classified intent")
    sources: Optional[List[str]] = Field(default_factory=list, description="Sources used for RAG")
    metadata: Optional[dict] = Field(default_factory=dict, description="Additional metadata")


@router.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest):
    """
    Chat endpoint for agent interactions

    Uses multi-agent orchestration with LangGraph to route requests
    to appropriate specialized agents (RAG, Tool, or Conversational).

    Args:
        request: Chat request with message and optional context

    Returns:
        ChatResponse: Agent response with metadata
    """
    try:
        logger.info(f"Received chat request: {request.message[:50]}...")

        # Convert history to agent message format
        conversation_history = [
            AgentMessage(role=msg.role, content=msg.content) for msg in request.history
        ]

        # Process through agent orchestration
        result = await orchestrator.process(
            user_message=request.message, conversation_history=conversation_history
        )

        # Generate or use existing conversation ID
        conversation_id = request.conversation_id or str(uuid.uuid4())

        return ChatResponse(
            message=result["message"],
            conversation_id=conversation_id,
            agent_type=result.get("agent_used", "unknown"),
            intent=result.get("intent"),
            sources=[],
            metadata={
                "timestamp": datetime.utcnow().isoformat(),
                **result.get("metadata", {}),
            },
        )

    except Exception as e:
        logger.error(f"Error processing chat request: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Error processing request")


@router.get("/conversations/{conversation_id}")
async def get_conversation(conversation_id: str):
    """
    Get conversation history

    Args:
        conversation_id: Conversation ID

    Returns:
        dict: Conversation history and metadata
    """
    # TODO: Implement conversation retrieval from database
    return {"conversation_id": conversation_id, "messages": [], "metadata": {}}
