"""Tool Agent for function calling"""

import json
from typing import Any, Dict, List

from langchain.prompts import ChatPromptTemplate
from langchain_openai import ChatOpenAI

from app.agents.base import BaseAgent
from app.agents.state import ConversationState, Message
from app.config import settings
from app.tools.registry import ToolRegistry
from app.tools.sample_tools import get_sample_tools


class ToolAgent(BaseAgent):
    """
    Tool Agent executes function calls to perform actions
    """

    TOOL_PROMPT = """You are a helpful assistant that can use tools to help users.

Available tools:
{tools}

User request: {request}

Instructions:
- Analyze if you need to use any tools to fulfill the request
- If yes, identify which tool(s) to use and extract the required parameters
- Respond in JSON format with tool calls

Response format:
{{
    "needs_tools": true/false,
    "tool_calls": [
        {{"tool": "tool_name", "parameters": {{...}}}}
    ],
    "reasoning": "Why these tools are needed"
}}

Response:"""

    def __init__(self):
        super().__init__("tool")
        self.llm = ChatOpenAI(
            model="gpt-4o-mini",
            temperature=0,
            openai_api_key=settings.openai_api_key,
        )
        self.prompt = ChatPromptTemplate.from_template(self.TOOL_PROMPT)
        self.tool_registry = ToolRegistry()

        # Register sample tools
        for tool_spec in get_sample_tools():
            self.tool_registry.register(
                name=tool_spec["name"],
                func=tool_spec["func"],
                description=tool_spec["description"],
                parameters=tool_spec["parameters"],
            )

    async def run(self, state: ConversationState) -> ConversationState:
        """
        Determine and execute necessary tools

        Args:
            state: Current conversation state

        Returns:
            Updated state with tool results
        """
        self.log_execution("tool_agent_start", {"intent": state.intent})

        # Get last user message
        user_message = next((msg for msg in reversed(state.messages) if msg.role == "user"), None)

        if not user_message:
            state.response = "I need more information to perform an action."
            state.next_step = "end"
            return state

        # Get tool descriptions
        tools_desc = "\n".join(
            [
                f"- {tool['name']}: {tool['description']}"
                for tool in self.tool_registry.get_all_tools()
            ]
        )

        try:
            # Determine which tools to use
            response = await self.llm.ainvoke(
                self.prompt.format_messages(tools=tools_desc, request=user_message.content)
            )

            # Parse tool planning response
            try:
                plan = json.loads(response.content)
            except json.JSONDecodeError:
                # Try to extract JSON from response
                content = response.content
                if "{" in content:
                    json_str = content[content.index("{") : content.rindex("}") + 1]
                    plan = json.loads(json_str)
                else:
                    raise ValueError("Could not parse tool planning response")

            if not plan.get("needs_tools", False):
                state.response = (
                    "I don't need to use any tools for this request. Let me help you directly."
                )
                state.next_step = "respond"
                return state

            # Execute tool calls
            tool_results = []
            for tool_call in plan.get("tool_calls", []):
                tool_name = tool_call.get("tool")
                parameters = tool_call.get("parameters", {})

                try:
                    result = await self.tool_registry.execute(tool_name, **parameters)
                    tool_results.append({"tool": tool_name, "success": True, "result": result})
                except Exception as e:
                    self.logger.error(f"Tool execution failed: {e}")
                    tool_results.append({"tool": tool_name, "success": False, "error": str(e)})

            state.tool_calls = tool_results

            # Generate response based on tool results
            results_summary = "\n".join(
                [
                    f"- {tr['tool']}: {json.dumps(tr.get('result', tr.get('error')))}"
                    for tr in tool_results
                ]
            )

            final_response = await self._generate_final_response(
                user_message.content, results_summary
            )

            state.response = final_response
            state.next_step = "end"

            # Add assistant message
            state.messages.append(
                Message(
                    role="assistant",
                    content=final_response,
                    metadata={
                        "agent": "tool",
                        "tools_used": [tc["tool"] for tc in tool_results],
                    },
                )
            )

            self.log_execution(
                "tools_executed",
                {"num_tools": len(tool_results), "tools": [tc["tool"] for tc in tool_results]},
            )

        except Exception as e:
            self.logger.error(f"Error in tool agent: {e}", exc_info=True)
            state.response = "I encountered an error while trying to help you. Please try rephrasing your request."
            state.next_step = "end"

        return state

    async def _generate_final_response(self, user_request: str, tool_results: str) -> str:
        """Generate final response based on tool results"""
        final_prompt = f"""User request: {user_request}

Tool execution results:
{tool_results}

Generate a natural, helpful response to the user based on these results.
Be concise and professional."""

        response = await self.llm.ainvoke(final_prompt)
        return response.content
