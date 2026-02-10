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
        """Load and add documents from data/documents directory"""
        import os
        from pathlib import Path

        # Path to documents directory
        docs_dir = Path(__file__).parent.parent.parent / "data" / "documents"

        if not docs_dir.exists():
            self.logger.warning(f"Documents directory not found: {docs_dir}")
            return

        try:
            documents = []
            # Load all .txt files from documents directory
            for file_path in docs_dir.glob("*.txt"):
                try:
                    with open(file_path, "r", encoding="utf-8") as f:
                        content = f.read().strip()
                        if content:
                            # Split long documents into chunks (max 500 chars for better retrieval)
                            chunks = self._chunk_text(content, max_length=500)
                            for chunk in chunks:
                                documents.append(
                                    {
                                        "text": chunk,
                                        "source": file_path.stem,
                                        "file": file_path.name,
                                    }
                                )
                except Exception as e:
                    self.logger.error(f"Error reading {file_path}: {e}")

            if not documents:
                self.logger.warning("No documents found to load")
                return

            # Create embeddings and upsert to Qdrant
            points = []
            for idx, doc in enumerate(documents):
                embedding = self.embeddings.embed_query(doc["text"])
                points.append(
                    PointStruct(
                        id=idx,
                        vector=embedding,
                        payload=doc,
                    )
                )

            self.qdrant.upsert(collection_name=self.collection_name, points=points)
            self.logger.info(
                f"Added {len(documents)} document chunks from {len(list(docs_dir.glob('*.txt')))} files"
            )
        except Exception as e:
            self.logger.error(f"Error adding documents: {e}")

    def _chunk_text(self, text: str, max_length: int = 500) -> List[str]:
        """Split text into chunks of approximately max_length characters"""
        # Split by paragraphs first
        paragraphs = [p.strip() for p in text.split("\n\n") if p.strip()]

        chunks = []
        current_chunk = ""

        for para in paragraphs:
            # If paragraph itself is longer than max_length, split it
            if len(para) > max_length:
                # If we have a current chunk, save it
                if current_chunk:
                    chunks.append(current_chunk.strip())
                    current_chunk = ""

                # Split long paragraph by sentences
                sentences = para.replace(". ", ".|").split("|")
                for sentence in sentences:
                    if len(current_chunk) + len(sentence) < max_length:
                        current_chunk += sentence + " "
                    else:
                        if current_chunk:
                            chunks.append(current_chunk.strip())
                        current_chunk = sentence + " "
            else:
                # Add paragraph to current chunk if it fits
                if len(current_chunk) + len(para) < max_length:
                    current_chunk += para + "\n\n"
                else:
                    # Save current chunk and start new one
                    if current_chunk:
                        chunks.append(current_chunk.strip())
                    current_chunk = para + "\n\n"

        # Add remaining chunk
        if current_chunk:
            chunks.append(current_chunk.strip())

        return chunks if chunks else [text]

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
