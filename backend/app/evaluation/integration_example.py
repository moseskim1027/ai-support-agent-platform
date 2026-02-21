"""
Integration Example: Adding RAGAS Monitoring to RAG Agent

This file demonstrates how to integrate RAGAS evaluation and Prometheus metrics
into an existing RAG agent implementation.

BEFORE: RAG agent without monitoring
AFTER: RAG agent with full RAGAS evaluation and metrics
"""

import time
from typing import List

from app.evaluation import EvaluationSample, RAGASEvaluator
from app.observability import track_rag_request

# ============================================================================
# BEFORE: Basic RAG Agent (No Monitoring)
# ============================================================================


class BasicRAGAgent:
    """RAG agent without monitoring"""

    async def query(self, question: str) -> str:
        # Retrieve contexts
        contexts = await self._retrieve(question)

        # Generate answer
        answer = await self._generate(question, contexts)

        return answer

    async def _retrieve(self, question: str) -> List[str]:
        # Retrieval logic here
        return ["context1", "context2"]

    async def _generate(self, question: str, contexts: List[str]) -> str:
        # Generation logic here
        return "Generated answer"


# ============================================================================
# AFTER: Monitored RAG Agent (With RAGAS + Prometheus)
# ============================================================================


class MonitoredRAGAgent:
    """RAG agent with full RAGAS evaluation and Prometheus metrics"""

    def __init__(self, llm, embeddings, model_name="gemini-2.5-flash-lite"):
        self.llm = llm
        self.embeddings = embeddings
        self.model_name = model_name

        # Initialize RAGAS evaluator
        self.ragas_evaluator = RAGASEvaluator(
            llm=llm,
            embeddings=embeddings,
            compute_without_ground_truth=True,
        )

    async def query(self, question: str) -> str:
        """
        Process a RAG query with full monitoring

        This method:
        1. Tracks overall request duration
        2. Records retrieval metrics
        3. Records generation metrics
        4. Computes and records RAGAS metrics
        5. Records success/failure status
        """
        # Use context manager for automatic tracking
        with track_rag_request(model_name=self.model_name) as recorder:
            try:
                # Stage 1: Retrieval
                retrieval_start = time.time()
                contexts, similarity_scores = await self._retrieve_with_scores(question)
                retrieval_duration = time.time() - retrieval_start

                # Record retrieval metrics
                recorder.record_retrieval_metrics(
                    duration=retrieval_duration,
                    num_contexts=len(contexts),
                    avg_similarity=(
                        sum(similarity_scores) / len(similarity_scores)
                        if similarity_scores
                        else 0.0
                    ),
                    retrieval_method="hybrid",
                    success=len(contexts) > 0,
                )

                # Stage 2: Generation
                generation_start = time.time()
                answer, token_info = await self._generate_with_tokens(question, contexts)
                generation_duration = time.time() - generation_start

                # Record generation metrics
                recorder.record_generation_metrics(
                    duration=generation_duration,
                    prompt_tokens=token_info["prompt_tokens"],
                    completion_tokens=token_info["completion_tokens"],
                )

                # Stage 3: RAGAS Evaluation
                evaluation_start = time.time()
                ragas_metrics = await self._evaluate_quality(question, contexts, answer)
                evaluation_duration = time.time() - evaluation_start

                # Record RAGAS metrics
                recorder.record_ragas_metrics(
                    ragas_metrics=ragas_metrics,
                    evaluation_duration=evaluation_duration,
                )

                return answer

            except Exception:
                # Error is automatically recorded by track_rag_request
                raise

    async def _retrieve_with_scores(self, question: str) -> tuple[list[str], list[float]]:
        """
        Retrieve contexts with similarity scores

        Returns:
            Tuple of (contexts, similarity_scores)
        """
        # Actual retrieval logic here
        # This is a simplified example
        contexts = ["context1", "context2", "context3"]
        similarity_scores = [0.89, 0.76, 0.65]

        return contexts, similarity_scores

    async def _generate_with_tokens(
        self, question: str, contexts: List[str]
    ) -> tuple[str, dict[str, int]]:
        """
        Generate answer and return token usage

        Returns:
            Tuple of (answer, token_info)
        """
        # Actual generation logic here
        # This is a simplified example
        answer = "Generated answer based on contexts"

        # Token info from LLM response
        token_info = {
            "prompt_tokens": 250,
            "completion_tokens": 50,
        }

        return answer, token_info

    async def _evaluate_quality(self, question: str, contexts: List[str], answer: str):
        """
        Evaluate response quality using RAGAS

        Returns:
            RAGASMetrics object
        """
        # Create evaluation sample
        sample = EvaluationSample(
            query=question,
            contexts=contexts,
            answer=answer,
            ground_truth=None,  # Optional: provide if available
        )

        # Compute RAGAS metrics
        metrics = await self.ragas_evaluator.evaluate(sample)

        return metrics


# ============================================================================
# Usage Examples
# ============================================================================


async def example_basic_usage():
    """Example 1: Basic monitored query"""
    from langchain_google_genai import ChatGoogleGenerativeAI, GoogleGenerativeAIEmbeddings

    from app.config import settings

    # Initialize LLM and embeddings
    llm = ChatGoogleGenerativeAI(
        model="gemini-2.5-flash-lite",
        google_api_key=settings.gemini_api_key,
    )
    embeddings = GoogleGenerativeAIEmbeddings(
        model="models/gemini-embedding-001",
        google_api_key=settings.gemini_api_key,
    )

    # Create monitored agent
    agent = MonitoredRAGAgent(llm=llm, embeddings=embeddings)

    # Process query (metrics automatically recorded)
    answer = await agent.query("What is your return policy?")
    print(f"Answer: {answer}")

    # Metrics are now available in Prometheus at /metrics endpoint


async def example_batch_processing():
    """Example 2: Process multiple queries with monitoring"""
    from langchain_google_genai import ChatGoogleGenerativeAI, GoogleGenerativeAIEmbeddings

    from app.config import settings

    llm = ChatGoogleGenerativeAI(
        model="gemini-2.5-flash-lite",
        google_api_key=settings.gemini_api_key,
    )
    embeddings = GoogleGenerativeAIEmbeddings(
        model="models/gemini-embedding-001",
        google_api_key=settings.gemini_api_key,
    )

    agent = MonitoredRAGAgent(llm=llm, embeddings=embeddings)

    queries = [
        "What is your return policy?",
        "How long does shipping take?",
        "Do you offer international shipping?",
    ]

    # Each query is monitored independently
    for query in queries:
        answer = await agent.query(query)
        print(f"Q: {query}")
        print(f"A: {answer}\n")

    # Check Prometheus metrics:
    # - Request count: rag_queries_total
    # - Average RAGAS scores: ragas_faithfulness_score, ragas_answer_relevancy_score
    # - Latency percentiles: rag_total_duration_seconds


async def example_custom_metrics():
    """Example 3: Adding custom business metrics"""
    from app.observability import track_rag_request

    # Placeholder functions for example
    async def retrieve_contexts(query: str):
        return ["context1", "context2"]

    async def generate_answer(query: str, contexts):
        return "Generated answer"

    with track_rag_request(model_name="custom-model") as recorder:
        # Standard RAG processing
        contexts = await retrieve_contexts("query")
        answer = await generate_answer("query", contexts)

        # Record standard metrics
        recorder.record_retrieval_metrics(
            duration=0.5,
            num_contexts=len(contexts),
            avg_similarity=0.85,
        )

        # You can also add custom logging/metrics here
        # Example: Track specific business events
        if "shipping" in answer.lower():
            # Custom metric for shipping-related queries
            pass


# ============================================================================
# Integration Checklist
# ============================================================================

"""
To integrate RAGAS monitoring into your RAG agent:

1. ✓ Add ragas to requirements.txt
2. ✓ Import evaluation and observability modules
3. ✓ Initialize RAGASEvaluator in your agent
4. ✓ Wrap queries with track_rag_request context manager
5. ✓ Record retrieval metrics after context retrieval
6. ✓ Record generation metrics after answer generation
7. ✓ Evaluate with RAGAS and record metrics
8. ✓ Configure Prometheus to scrape /metrics endpoint
9. ✓ Import Grafana dashboard from infrastructure/grafana/
10. ✓ Set up alerts based on metric thresholds

Done! Your RAG agent is now fully monitored.
"""


# ============================================================================
# Performance Notes
# ============================================================================

"""
Performance Impact of Monitoring:

1. Retrieval Metrics: ~1-5ms overhead (negligible)
2. Generation Metrics: ~1-5ms overhead (negligible)
3. RAGAS Evaluation: ~1-5 seconds (significant)
   - Faithfulness: ~0.5-2s
   - Answer Relevancy: ~0.5-2s
   - Context Precision/Recall: ~1-3s (with ground truth)

Total Overhead: ~1-5 seconds per request

Mitigation Strategies:
- Run RAGAS evaluation asynchronously (non-blocking)
- Sample evaluation (e.g., evaluate 10% of requests)
- Batch evaluation offline for historical analysis
- Use faster LLM for evaluation (separate from generation)

Example: Async evaluation (fire-and-forget)
```python
# Don't await evaluation
asyncio.create_task(self._evaluate_quality(question, contexts, answer))

# Or sample
if random.random() < 0.1:  # 10% sampling
    await self._evaluate_quality(question, contexts, answer)
```
"""
