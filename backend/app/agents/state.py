"""State management for agent orchestration"""

import operator
from datetime import datetime
from typing import Annotated, Any, Dict, List, Optional

from pydantic import BaseModel, Field


class Message(BaseModel):
    """Message in conversation"""

    role: str = Field(..., description="Message role: user, assistant, system")
    content: str = Field(..., description="Message content")
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    metadata: Dict[str, Any] = Field(default_factory=dict)


class AgentState(BaseModel):
    """State for individual agent"""

    messages: List[Message] = Field(default_factory=list)
    current_agent: str = Field(default="router")
    intent: Optional[str] = None
    context: Dict[str, Any] = Field(default_factory=dict)


class ConversationState(BaseModel):
    """Overall conversation state for LangGraph"""

    messages: Annotated[List[Message], operator.add] = Field(default_factory=list)
    current_agent: str = Field(default="router")
    intent: Optional[str] = None
    tool_calls: List[Dict[str, Any]] = Field(default_factory=list)
    retrieved_docs: List[str] = Field(default_factory=list)
    response: Optional[str] = None
    next_step: Optional[str] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)

    class Config:
        arbitrary_types_allowed = True
