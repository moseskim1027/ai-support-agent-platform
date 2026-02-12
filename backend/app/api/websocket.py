"""WebSocket endpoint for real-time streaming chat"""

import asyncio
import json
import logging
import uuid
from typing import Optional

from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from sqlalchemy.ext.asyncio import AsyncSession

from app.agents.state import Message as AgentMessage
from app.database import AsyncSessionLocal
from app.database.repositories import ConversationRepository
from app.orchestration import AgentOrchestrator

router = APIRouter()
logger = logging.getLogger(__name__)

# Initialize orchestrator (singleton)
orchestrator = AgentOrchestrator()


class ConnectionManager:
    """Manages WebSocket connections"""

    def __init__(self):
        self.active_connections: dict[str, WebSocket] = {}

    async def connect(self, websocket: WebSocket, client_id: str):
        """Accept and register a new WebSocket connection"""
        await websocket.accept()
        self.active_connections[client_id] = websocket
        total = len(self.active_connections)
        logger.info(f"WebSocket client {client_id} connected. Total: {total}")

    def disconnect(self, client_id: str):
        """Remove a WebSocket connection"""
        if client_id in self.active_connections:
            del self.active_connections[client_id]
            total = len(self.active_connections)
            logger.info(f"WebSocket client {client_id} disconnected. Total: {total}")

    async def send_message(self, message: dict, client_id: str):
        """Send a message to a specific client"""
        if client_id in self.active_connections:
            await self.active_connections[client_id].send_json(message)

    async def send_text(self, text: str, client_id: str):
        """Send text to a specific client"""
        if client_id in self.active_connections:
            await self.active_connections[client_id].send_text(text)


manager = ConnectionManager()


async def stream_agent_response(
    message: str,
    conversation_id: Optional[str],
    client_id: str,
    db: AsyncSession,
):
    """
    Process message and stream response in real-time

    Args:
        message: User message
        conversation_id: Optional conversation ID
        client_id: WebSocket client ID
        db: Database session
    """
    try:
        repo = ConversationRepository(db)

        # Get or create conversation
        if conversation_id:
            conv_uuid = uuid.UUID(conversation_id)
            conversation = await repo.get_conversation(conv_uuid, include_messages=True)

            if conversation:
                conversation_history = [
                    AgentMessage(role=msg.role, content=msg.content)
                    for msg in conversation.messages
                ]
            else:
                conversation = await repo.create_conversation(conversation_id=conv_uuid)
                conversation_history = []
        else:
            conversation = await repo.create_conversation()
            conversation_history = []

        # Add user message to database
        await repo.add_message(
            conversation_id=conversation.id,
            role="user",
            content=message,
        )

        # Send acknowledgment
        await manager.send_message(
            {
                "type": "conversation_id",
                "conversation_id": str(conversation.id),
            },
            client_id,
        )

        # Send "thinking" status
        await manager.send_message(
            {
                "type": "status",
                "status": "processing",
                "message": "Processing your request...",
            },
            client_id,
        )

        # Process through agent orchestration
        result = await orchestrator.process(
            user_message=message,
            conversation_history=conversation_history,
        )

        # Stream the response word by word for demonstration
        # In production, you'd integrate with streaming LLM APIs
        response_text = result["message"]
        words = response_text.split()

        for i, word in enumerate(words):
            # Send word chunks
            await manager.send_message(
                {
                    "type": "chunk",
                    "content": word + " ",
                    "is_final": i == len(words) - 1,
                },
                client_id,
            )
            # Small delay to simulate streaming (remove in production with real streaming)
            await asyncio.sleep(0.05)

        # Send completion message
        await manager.send_message(
            {
                "type": "complete",
                "agent_type": result.get("agent_used", "unknown"),
                "intent": result.get("intent"),
                "sources": result.get("sources", []),
                "metadata": result.get("metadata", {}),
            },
            client_id,
        )

        # Add assistant response to database
        await repo.add_message(
            conversation_id=conversation.id,
            role="assistant",
            content=response_text,
            agent_type=result.get("agent_used"),
            intent=result.get("intent"),
            sources=result.get("sources", []),
            metadata=result.get("metadata", {}),
        )

        await db.commit()

    except Exception as e:
        logger.error(f"Error in stream_agent_response: {e}", exc_info=True)
        await manager.send_message(
            {
                "type": "error",
                "error": str(e),
                "message": "An error occurred while processing your request",
            },
            client_id,
        )
        await db.rollback()


@router.websocket("/ws/chat")
async def websocket_chat(websocket: WebSocket):
    """
    WebSocket endpoint for streaming chat

    Protocol:
        Client -> Server:
            {
                "type": "message",
                "message": "user message",
                "conversation_id": "optional-uuid"
            }

        Server -> Client:
            {
                "type": "conversation_id",
                "conversation_id": "uuid"
            }
            {
                "type": "status",
                "status": "processing",
                "message": "Processing your request..."
            }
            {
                "type": "chunk",
                "content": "word ",
                "is_final": false
            }
            {
                "type": "complete",
                "agent_type": "rag",
                "intent": "knowledge",
                "sources": [],
                "metadata": {}
            }
            {
                "type": "error",
                "error": "error message",
                "message": "human readable message"
            }
    """
    client_id = str(uuid.uuid4())
    await manager.connect(websocket, client_id)

    try:
        # Send welcome message
        await manager.send_message(
            {
                "type": "connected",
                "client_id": client_id,
                "message": "Connected to AI Support Agent",
            },
            client_id,
        )

        while True:
            # Receive message from client
            data = await websocket.receive_text()

            try:
                message_data = json.loads(data)
            except json.JSONDecodeError:
                await manager.send_message(
                    {
                        "type": "error",
                        "error": "Invalid JSON",
                        "message": "Please send valid JSON",
                    },
                    client_id,
                )
                continue

            message_type = message_data.get("type")

            if message_type == "message":
                user_message = message_data.get("message", "").strip()
                conversation_id = message_data.get("conversation_id")

                if not user_message:
                    await manager.send_message(
                        {
                            "type": "error",
                            "error": "Empty message",
                            "message": "Message cannot be empty",
                        },
                        client_id,
                    )
                    continue

                # Process message in database session
                async with AsyncSessionLocal() as db:
                    await stream_agent_response(
                        message=user_message,
                        conversation_id=conversation_id,
                        client_id=client_id,
                        db=db,
                    )

            elif message_type == "ping":
                await manager.send_message({"type": "pong"}, client_id)

            else:
                await manager.send_message(
                    {
                        "type": "error",
                        "error": "Unknown message type",
                        "message": f"Unknown message type: {message_type}",
                    },
                    client_id,
                )

    except WebSocketDisconnect:
        manager.disconnect(client_id)
        logger.info(f"Client {client_id} disconnected normally")
    except Exception as e:
        logger.error(f"WebSocket error for client {client_id}: {e}", exc_info=True)
        manager.disconnect(client_id)
