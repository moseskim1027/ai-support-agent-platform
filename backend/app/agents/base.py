"""Base agent class"""

import logging
from abc import ABC, abstractmethod
from typing import Any, Dict

from app.agents.state import ConversationState

logger = logging.getLogger(__name__)


class BaseAgent(ABC):
    """Base class for all agents"""

    def __init__(self, name: str):
        self.name = name
        self.logger = logging.getLogger(f"agent.{name}")

    @abstractmethod
    async def run(self, state: ConversationState) -> ConversationState:
        """
        Execute agent logic

        Args:
            state: Current conversation state

        Returns:
            Updated conversation state
        """
        pass

    def log_execution(self, action: str, details: Dict[str, Any]):
        """Log agent execution for observability"""
        self.logger.info(f"Agent: {self.name} | Action: {action} | Details: {details}")
