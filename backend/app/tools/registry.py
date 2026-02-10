"""Tool registry for managing available tools"""

import logging
from typing import Any, Callable, Dict, List

logger = logging.getLogger(__name__)


class ToolRegistry:
    """Registry for managing and executing tools"""

    def __init__(self):
        self.tools: Dict[str, Callable] = {}
        self.tool_descriptions: Dict[str, Dict[str, Any]] = {}

    def register(self, name: str, func: Callable, description: str, parameters: Dict[str, Any]):
        """
        Register a tool

        Args:
            name: Tool name
            func: Tool function
            description: Tool description
            parameters: JSON schema for parameters
        """
        self.tools[name] = func
        self.tool_descriptions[name] = {
            "name": name,
            "description": description,
            "parameters": parameters,
        }
        logger.info(f"Registered tool: {name}")

    def get_tool(self, name: str) -> Callable:
        """Get tool function by name"""
        return self.tools.get(name)

    def get_all_tools(self) -> List[Dict[str, Any]]:
        """Get all tool descriptions for LLM"""
        return list(self.tool_descriptions.values())

    async def execute(self, name: str, **kwargs) -> Any:
        """
        Execute a tool

        Args:
            name: Tool name
            **kwargs: Tool parameters

        Returns:
            Tool execution result
        """
        tool = self.get_tool(name)
        if not tool:
            raise ValueError(f"Tool not found: {name}")

        try:
            logger.info(f"Executing tool: {name} with params: {kwargs}")
            result = await tool(**kwargs) if tool.__code__.co_flags & 0x80 else tool(**kwargs)
            logger.info(f"Tool {name} executed successfully")
            return result
        except Exception as e:
            logger.error(f"Error executing tool {name}: {e}", exc_info=True)
            raise
