"""Repository layer for database operations"""

import uuid
from datetime import datetime
from typing import List, Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.database.models import Conversation, ConversationMessage


class ConversationRepository:
    """Repository for conversation operations"""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def create_conversation(
        self, conversation_id: Optional[uuid.UUID] = None, user_id: Optional[str] = None
    ) -> Conversation:
        """Create a new conversation"""
        conversation = Conversation(
            id=conversation_id or uuid.uuid4(),
            user_id=user_id,
            conv_metadata={},
        )
        self.db.add(conversation)
        await self.db.flush()
        return conversation

    async def get_conversation(
        self, conversation_id: uuid.UUID, include_messages: bool = True
    ) -> Optional[Conversation]:
        """Get a conversation by ID"""
        query = select(Conversation).where(Conversation.id == conversation_id)

        if include_messages:
            query = query.options(selectinload(Conversation.messages))

        result = await self.db.execute(query)
        return result.scalar_one_or_none()

    async def add_message(
        self,
        conversation_id: uuid.UUID,
        role: str,
        content: str,
        agent_type: Optional[str] = None,
        intent: Optional[str] = None,
        sources: Optional[List[str]] = None,
        metadata: Optional[dict] = None,
    ) -> ConversationMessage:
        """Add a message to a conversation"""
        message = ConversationMessage(
            conversation_id=conversation_id,
            role=role,
            content=content,
            agent_type=agent_type,
            intent=intent,
            sources=sources or [],
            metadata=metadata or {},
        )
        self.db.add(message)
        await self.db.flush()
        return message

    async def get_conversation_messages(
        self, conversation_id: uuid.UUID, limit: Optional[int] = None
    ) -> List[ConversationMessage]:
        """Get messages for a conversation"""
        query = (
            select(ConversationMessage)
            .where(ConversationMessage.conversation_id == conversation_id)
            .order_by(ConversationMessage.created_at.asc())
        )

        if limit:
            query = query.limit(limit)

        result = await self.db.execute(query)
        return list(result.scalars().all())

    async def update_conversation_title(
        self, conversation_id: uuid.UUID, title: str
    ) -> Optional[Conversation]:
        """Update conversation title"""
        conversation = await self.get_conversation(conversation_id, include_messages=False)
        if conversation:
            conversation.title = title
            conversation.updated_at = datetime.utcnow()
            await self.db.flush()
        return conversation

    async def delete_conversation(self, conversation_id: uuid.UUID) -> bool:
        """Delete a conversation and its messages"""
        conversation = await self.get_conversation(conversation_id, include_messages=False)
        if conversation:
            await self.db.delete(conversation)
            await self.db.flush()
            return True
        return False

    async def list_conversations(
        self, user_id: Optional[str] = None, limit: int = 50, offset: int = 0
    ) -> List[Conversation]:
        """List conversations, optionally filtered by user"""
        query = select(Conversation).order_by(Conversation.updated_at.desc())

        if user_id:
            query = query.where(Conversation.user_id == user_id)

        query = query.limit(limit).offset(offset)

        result = await self.db.execute(query)
        return list(result.scalars().all())
