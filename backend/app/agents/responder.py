"""Response Agent for general conversation"""

from langchain.prompts import ChatPromptTemplate
from langchain_google_genai import ChatGoogleGenerativeAI

from app.agents.base import BaseAgent
from app.agents.state import ConversationState, Message
from app.config import settings


class ResponderAgent(BaseAgent):
    """
    Responder Agent handles general conversation and generates responses
    """

    CONVERSATION_PROMPT = """You are a friendly and professional customer support assistant.

Conversation history:
{history}

User message: {message}

Instructions:
- Be warm, professional, and helpful
- For greetings, respond appropriately
- For thanks, acknowledge politely
- For unclear requests, ask clarifying questions
- Keep responses concise and natural

Response:"""

    def __init__(self):
        super().__init__("responder")
        # Using Gemini 2.5 Flash Lite (free tier) for conversational responses
        self.llm = ChatGoogleGenerativeAI(
            model="gemini-2.5-flash-lite",
            temperature=0.7,
            google_api_key=settings.gemini_api_key,
        )
        self.prompt = ChatPromptTemplate.from_template(self.CONVERSATION_PROMPT)

    async def run(self, state: ConversationState) -> ConversationState:
        """
        Generate conversational response

        Args:
            state: Current conversation state

        Returns:
            Updated state with response
        """
        self.log_execution("responder_start", {"intent": state.intent})

        # Get last user message
        user_message = next((msg for msg in reversed(state.messages) if msg.role == "user"), None)

        if not user_message:
            state.response = "Hello! How can I help you today?"
            state.next_step = "end"
            return state

        # Build conversation history context
        history_messages = state.messages[-5:]  # Last 5 messages for context
        history = "\n".join([f"{msg.role}: {msg.content}" for msg in history_messages[:-1]])

        try:
            response = await self.llm.ainvoke(
                self.prompt.format_messages(
                    history=history if history else "No previous conversation",
                    message=user_message.content,
                )
            )

            state.response = response.content
            state.next_step = "end"

            # Add assistant message to state
            state.messages.append(
                Message(
                    role="assistant",
                    content=response.content,
                    metadata={"agent": "responder"},
                )
            )

            self.log_execution("response_generated", {"response_length": len(response.content)})

        except Exception as e:
            self.logger.error(f"Error generating response: {e}", exc_info=True)
            state.response = "Hello! How can I assist you today?"
            state.next_step = "end"

        return state
