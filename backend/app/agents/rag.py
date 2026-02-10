"""RAG Agent for knowledge retrieval"""

from typing import List

from langchain.prompts import ChatPromptTemplate
from langchain_openai import ChatOpenAI, OpenAIEmbeddings
from qdrant_client import QdrantClient
from qdrant_client.models import Distance, PointStruct, VectorParams

from app.agents.base import BaseAgent
from app.agents.state import ConversationState, Message
from app.config import settings


class RAGAgent(BaseAgent):
    """
    RAG Agent retrieves relevant information from knowledge base and generates responses
    """

    RAG_PROMPT = """You are a helpful customer support assistant.
Answer the user's question based on the provided context from the knowledge base.

Context from knowledge base:
{context}

User question: {question}

Instructions:
- Provide a clear, concise answer based on the context
- If the context doesn't contain relevant information, say so politely
- Cite the source when possible
- Be professional and helpful

Answer:"""

    def __init__(self):
        super().__init__("rag")
        self.llm = ChatOpenAI(
            model="gpt-4o-mini",
            temperature=0.3,
            openai_api_key=settings.openai_api_key,
        )
        self.embeddings = OpenAIEmbeddings(openai_api_key=settings.openai_api_key)
        self.prompt = ChatPromptTemplate.from_template(self.RAG_PROMPT)

        # Initialize Qdrant client
        try:
            self.qdrant = QdrantClient(url=settings.qdrant_url)
            self.collection_name = "knowledge_base"
            self._initialize_collection()
        except Exception as e:
            self.logger.warning(f"Qdrant not available: {e}")
            self.qdrant = None

    def _initialize_collection(self):
        """Create collection if it doesn't exist"""
        try:
            collections = self.qdrant.get_collections().collections
            collection_names = [c.name for c in collections]

            if self.collection_name not in collection_names:
                self.qdrant.create_collection(
                    collection_name=self.collection_name,
                    vectors_config=VectorParams(size=1536, distance=Distance.COSINE),
                )
                self.logger.info(f"Created collection: {self.collection_name}")

                # Add sample documents
                self._add_sample_documents()
        except Exception as e:
            self.logger.error(f"Error initializing collection: {e}")

    def _add_sample_documents(self):
        """Add sample knowledge base documents"""
        sample_docs = [
            "Our return policy allows returns within 30 days of purchase. Items must be unused and in original packaging.",
            "To reset your password, go to Settings > Account > Reset Password. You will receive an email with instructions.",
            "We offer 24/7 customer support via chat, email, and phone. Premium members get priority support.",
            "Shipping is free for orders over $50. Standard shipping takes 3-5 business days.",
            "Our AI agent platform supports multiple languages including English, Spanish, French, German, and Japanese.",
        ]

        try:
            points = []
            for idx, doc in enumerate(sample_docs):
                embedding = self.embeddings.embed_query(doc)
                points.append(
                    PointStruct(
                        id=idx,
                        vector=embedding,
                        payload={"text": doc, "source": "sample_kb"},
                    )
                )

            self.qdrant.upsert(collection_name=self.collection_name, points=points)
            self.logger.info(f"Added {len(sample_docs)} sample documents")
        except Exception as e:
            self.logger.error(f"Error adding sample documents: {e}")

    async def retrieve(self, query: str, top_k: int = 3) -> List[str]:
        """
        Retrieve relevant documents from knowledge base

        Args:
            query: User query
            top_k: Number of documents to retrieve

        Returns:
            List of relevant document texts
        """
        if not self.qdrant:
            return []

        try:
            # Generate query embedding
            query_embedding = self.embeddings.embed_query(query)

            # Search in Qdrant
            results = self.qdrant.search(
                collection_name=self.collection_name,
                query_vector=query_embedding,
                limit=top_k,
            )

            # Extract document texts
            documents = [hit.payload["text"] for hit in results if hit.score > 0.7]

            self.log_execution(
                "retrieve_documents",
                {"query": query[:50], "num_docs": len(documents)},
            )

            return documents

        except Exception as e:
            self.logger.error(f"Error retrieving documents: {e}", exc_info=True)
            return []

    async def run(self, state: ConversationState) -> ConversationState:
        """
        Retrieve relevant documents and generate response

        Args:
            state: Current conversation state

        Returns:
            Updated state with retrieved docs and response
        """
        self.log_execution("rag_agent_start", {"intent": state.intent})

        # Get last user message
        user_message = next((msg for msg in reversed(state.messages) if msg.role == "user"), None)

        if not user_message:
            state.response = "I'm sorry, I didn't receive a question."
            state.next_step = "end"
            return state

        # Retrieve relevant documents
        documents = await self.retrieve(user_message.content)
        state.retrieved_docs = documents

        # Generate response using retrieved context
        try:
            context = (
                "\n\n".join(documents)
                if documents
                else "No relevant information found in knowledge base."
            )

            response = await self.llm.ainvoke(
                self.prompt.format_messages(context=context, question=user_message.content)
            )

            state.response = response.content
            state.next_step = "end"

            # Add assistant message to state
            state.messages.append(
                Message(
                    role="assistant",
                    content=response.content,
                    metadata={"agent": "rag", "num_docs_retrieved": len(documents)},
                )
            )

            self.log_execution(
                "rag_response_generated",
                {"response_length": len(response.content), "docs_used": len(documents)},
            )

        except Exception as e:
            self.logger.error(f"Error generating RAG response: {e}", exc_info=True)
            state.response = "I apologize, but I encountered an error processing your request."
            state.next_step = "end"

        return state
