"""Chat API endpoints"""

import logging
import uuid
from datetime import datetime
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from app.agents.state import Message as AgentMessage
from app.database import get_db
from app.database.repositories import ConversationRepository
from app.middleware import limiter
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
@limiter.limit("20/minute")
async def chat(req: Request, request: ChatRequest, db: AsyncSession = Depends(get_db)):
    """
    Chat endpoint for agent interactions

    Uses multi-agent orchestration with LangGraph to route requests
    to appropriate specialized agents (RAG, Tool, or Conversational).

    Args:
        request: Chat request with message and optional context
        db: Database session

    Returns:
        ChatResponse: Agent response with metadata
    """
    try:
        logger.info(f"Received chat request: {request.message[:50]}...")

        repo = ConversationRepository(db)

        # Get or create conversation
        if request.conversation_id:
            conv_uuid = uuid.UUID(request.conversation_id)
            conversation = await repo.get_conversation(conv_uuid, include_messages=True)

            if conversation:
                # Load history from database
                conversation_history = [
                    AgentMessage(role=msg.role, content=msg.content)
                    for msg in conversation.messages
                ]
            else:
                # Create new conversation if ID doesn't exist
                conversation = await repo.create_conversation(conversation_id=conv_uuid)
                conversation_history = []
        else:
            # Create new conversation
            conversation = await repo.create_conversation()
            conversation_history = []

        # Add user message to database
        await repo.add_message(
            conversation_id=conversation.id,
            role="user",
            content=request.message,
        )

        # Process through agent orchestration
        result = await orchestrator.process(
            user_message=request.message, conversation_history=conversation_history
        )

        # Add assistant response to database
        await repo.add_message(
            conversation_id=conversation.id,
            role="assistant",
            content=result["message"],
            agent_type=result.get("agent_used"),
            intent=result.get("intent"),
            sources=result.get("sources", []),
            metadata=result.get("metadata", {}),
        )

        # Commit the transaction
        await db.commit()

        return ChatResponse(
            message=result["message"],
            conversation_id=str(conversation.id),
            agent_type=result.get("agent_used", "unknown"),
            intent=result.get("intent"),
            sources=result.get("sources", []),
            metadata={
                "timestamp": datetime.utcnow().isoformat(),
                **result.get("metadata", {}),
            },
        )

    except Exception as e:
        logger.error(f"Error processing chat request: {e}", exc_info=True)
        await db.rollback()
        raise HTTPException(status_code=500, detail="Error processing request")


@router.get("/conversations/{conversation_id}")
async def get_conversation(conversation_id: str, db: AsyncSession = Depends(get_db)):
    """
    Get conversation history

    Args:
        conversation_id: Conversation ID
        db: Database session

    Returns:
        dict: Conversation history and metadata
    """
    try:
        repo = ConversationRepository(db)
        conv_uuid = uuid.UUID(conversation_id)
        conversation = await repo.get_conversation(conv_uuid, include_messages=True)

        if not conversation:
            raise HTTPException(status_code=404, detail="Conversation not found")

        messages = [
            {
                "id": str(msg.id),
                "role": msg.role,
                "content": msg.content,
                "agent_type": msg.agent_type,
                "intent": msg.intent,
                "sources": msg.sources,
                "metadata": msg.metadata,
                "created_at": msg.created_at.isoformat(),
            }
            for msg in conversation.messages
        ]

        return {
            "conversation_id": str(conversation.id),
            "user_id": conversation.user_id,
            "title": conversation.title,
            "messages": messages,
            "metadata": conversation.metadata,
            "created_at": conversation.created_at.isoformat(),
            "updated_at": conversation.updated_at.isoformat(),
        }

    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid conversation ID format")
    except Exception as e:
        logger.error(f"Error retrieving conversation: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Error retrieving conversation")
