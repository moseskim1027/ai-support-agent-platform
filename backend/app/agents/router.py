"""Router Agent for intent classification"""

from langchain.prompts import ChatPromptTemplate
from langchain_openai import ChatOpenAI

from app.agents.base import BaseAgent
from app.agents.state import ConversationState
from app.config import settings


class RouterAgent(BaseAgent):
    """
    Router Agent classifies user intent and routes to appropriate specialized agent

    Routes:
    - knowledge: Questions requiring information retrieval (RAG)
    - action: Requests requiring tool execution (order lookup, refunds, etc.)
    - conversation: General conversation, greetings, chitchat
    """

    ROUTING_PROMPT = """You are an intelligent routing agent for a customer support system.
Analyze the user's message and classify the intent into one of these categories:

1. **knowledge**: User is asking a question that requires retrieving information
   from the knowledge base
   Examples: "How do I reset my password?", "What are your return policies?"

2. **action**: User wants to perform an action or needs tool execution
   Examples: "Check my order status", "Cancel my subscription"

3. **conversation**: General conversation, greetings, or chitchat
   Examples: "Hello", "Thanks for your help", "How are you?"

User message: {message}

Respond with ONLY the category name (knowledge, action, or conversation) and a brief reasoning.
Format: category|reasoning
"""

    def __init__(self):
        super().__init__("router")
        self.llm = ChatOpenAI(
            model="gpt-4o-mini",
            temperature=0,
            openai_api_key=settings.openai_api_key,
        )
        self.prompt = ChatPromptTemplate.from_template(self.ROUTING_PROMPT)

    async def run(self, state: ConversationState) -> ConversationState:
        """
        Classify intent and determine next agent

        Args:
            state: Current conversation state

        Returns:
            Updated state with intent and next agent
        """
        self.log_execution("classify_intent", {"message_count": len(state.messages)})

        # Get last user message
        user_message = next((msg for msg in reversed(state.messages) if msg.role == "user"), None)

        if not user_message:
            state.intent = "conversation"
            state.next_step = "respond"
            return state

        # Classify intent using LLM
        try:
            response = await self.llm.ainvoke(
                self.prompt.format_messages(message=user_message.content)
            )

            # Parse response
            result = response.content.strip()
            if "|" in result:
                intent, reasoning = result.split("|", 1)
                intent = intent.strip().lower()
            else:
                intent = result.strip().lower()
                reasoning = "No reasoning provided"

            # Validate intent
            valid_intents = ["knowledge", "action", "conversation"]
            if intent not in valid_intents:
                self.logger.warning(f"Invalid intent '{intent}', defaulting to conversation")
                intent = "conversation"

            state.intent = intent
            state.metadata["routing_reasoning"] = reasoning

            # Determine next agent
            next_agent_map = {
                "knowledge": "rag",
                "action": "tool",
                "conversation": "respond",
            }
            state.next_step = next_agent_map.get(intent, "respond")

            self.log_execution(
                "intent_classified",
                {"intent": intent, "next_step": state.next_step, "reasoning": reasoning},
            )

        except Exception as e:
            self.logger.error(f"Error classifying intent: {e}", exc_info=True)
            state.intent = "conversation"
            state.next_step = "respond"

        return state
