"""
RAGAS-Based Evaluation Metrics Module

This module implements RAGAS (Retrieval-Augmented Generation Assessment) metrics
for evaluating RAG system performance.

Metrics computed:
- Faithfulness: Whether the answer is grounded in the retrieved context
- Answer Relevancy: How relevant the answer is to the user's question
- Context Precision: Precision of retrieved contexts (requires ground truth)
- Context Recall: Recall of retrieved contexts (requires ground truth)

Usage:
    evaluator = RAGASEvaluator(llm, embeddings)
    sample = EvaluationSample(
        query="What is the return policy?",
        contexts=["Returns accepted within 30 days..."],
        answer="You can return items within 30 days.",
        ground_truth="Returns accepted within 30 days"  # Optional
    )
    metrics = await evaluator.evaluate(sample)
"""

import logging
from dataclasses import dataclass
from typing import Dict, List, Optional

from datasets import Dataset
from langchain_core.embeddings import Embeddings
from langchain_core.language_models import BaseLanguageModel
from ragas import evaluate
from ragas.metrics import (
    answer_relevancy,
    context_precision,
    context_recall,
    faithfulness,
)

logger = logging.getLogger(__name__)


@dataclass
class EvaluationSample:
    """
    A single sample for RAGAS evaluation

    Args:
        query: User's question/query
        contexts: List of retrieved context chunks
        answer: Generated answer from the RAG system
        ground_truth: Optional ground truth answer for precision/recall metrics
    """

    query: str
    contexts: List[str]
    answer: str
    ground_truth: Optional[str] = None


@dataclass
class RAGASMetrics:
    """
    Container for RAGAS metric results

    Attributes:
        faithfulness: Score 0-1, measures if answer is grounded in context
        answer_relevancy: Score 0-1, measures answer relevance to query
        context_precision: Score 0-1, precision of retrieved contexts (needs ground truth)
        context_recall: Score 0-1, recall of retrieved contexts (needs ground truth)
    """

    faithfulness: Optional[float] = None
    answer_relevancy: Optional[float] = None
    context_precision: Optional[float] = None
    context_recall: Optional[float] = None

    def to_dict(self) -> Dict[str, float]:
        """Convert metrics to dictionary, excluding None values"""
        return {k: v for k, v in self.__dict__.items() if v is not None}


class RAGASEvaluator:
    """
    RAGAS-based evaluation system for RAG pipelines

    This evaluator computes multiple quality metrics for retrieval-augmented
    generation systems using the RAGAS framework.

    The module is designed to be:
    - Modular: Easy to add new metrics
    - Production-ready: Handles errors gracefully
    - Observable: Integrates with monitoring systems
    """

    def __init__(
        self,
        llm: BaseLanguageModel,
        embeddings: Embeddings,
        compute_without_ground_truth: bool = True,
    ):
        """
        Initialize RAGAS evaluator

        Args:
            llm: Language model for metric computation
            embeddings: Embedding model for similarity calculations
            compute_without_ground_truth: If True, compute metrics that
                don't require ground truth even when it's not provided
        """
        self.llm = llm
        self.embeddings = embeddings
        self.compute_without_ground_truth = compute_without_ground_truth

        # Metrics that require ground truth
        self.metrics_with_ground_truth = [
            faithfulness,
            answer_relevancy,
            context_precision,
            context_recall,
        ]

        # Metrics that work without ground truth
        self.metrics_without_ground_truth = [
            faithfulness,
            answer_relevancy,
        ]

    async def evaluate(self, sample: EvaluationSample) -> RAGASMetrics:
        """
        Evaluate a single RAG sample using RAGAS metrics

        Args:
            sample: Evaluation sample with query, contexts, answer, and optional ground truth

        Returns:
            RAGASMetrics object with computed scores

        Note:
            - Faithfulness and Answer Relevancy always computed
            - Context Precision and Recall require ground truth
            - Errors in individual metrics don't fail the entire evaluation
        """
        try:
            # Prepare dataset
            data = {
                "question": [sample.query],
                "contexts": [sample.contexts],
                "answer": [sample.answer],
            }

            # Determine which metrics to compute
            if sample.ground_truth:
                data["ground_truth"] = [sample.ground_truth]
                metrics_to_compute = self.metrics_with_ground_truth
            elif self.compute_without_ground_truth:
                metrics_to_compute = self.metrics_without_ground_truth
            else:
                logger.warning("No ground truth provided and compute_without_ground_truth=False")
                return RAGASMetrics()

            # Create dataset
            dataset = Dataset.from_dict(data)

            # Compute metrics
            # Note: RAGAS evaluate() is synchronous, but we wrap in async for consistency
            result = evaluate(
                dataset,
                metrics=metrics_to_compute,
                llm=self.llm,
                embeddings=self.embeddings,
            )

            # Extract metrics
            metrics = RAGASMetrics(
                faithfulness=result.get("faithfulness"),
                answer_relevancy=result.get("answer_relevancy"),
                context_precision=result.get("context_precision") if sample.ground_truth else None,
                context_recall=result.get("context_recall") if sample.ground_truth else None,
            )

            logger.debug(f"RAGAS evaluation completed: {metrics.to_dict()}")
            return metrics

        except Exception as e:
            logger.error(f"Error computing RAGAS metrics: {e}", exc_info=True)
            # Return empty metrics on error rather than failing
            return RAGASMetrics()

    async def evaluate_batch(
        self, samples: List[EvaluationSample]
    ) -> List[RAGASMetrics]:
        """
        Evaluate multiple samples efficiently

        Args:
            samples: List of evaluation samples

        Returns:
            List of RAGASMetrics, one per sample

        Note:
            This method processes samples individually to isolate failures.
            For production use with many samples, consider implementing
            true batch processing for efficiency.
        """
        results = []
        for sample in samples:
            metrics = await self.evaluate(sample)
            results.append(metrics)
        return results


# Convenience function for quick evaluation
async def evaluate_rag_output(
    query: str,
    contexts: List[str],
    answer: str,
    llm: BaseLanguageModel,
    embeddings: Embeddings,
    ground_truth: Optional[str] = None,
) -> Dict[str, float]:
    """
    Convenience function for quick RAGAS evaluation

    Args:
        query: User's question
        contexts: Retrieved context chunks
        answer: Generated answer
        llm: Language model
        embeddings: Embedding model
        ground_truth: Optional ground truth answer

    Returns:
        Dictionary of metric names to scores

    Example:
        >>> metrics = await evaluate_rag_output(
        ...     query="What is the return policy?",
        ...     contexts=["Returns within 30 days..."],
        ...     answer="You can return within 30 days",
        ...     llm=my_llm,
        ...     embeddings=my_embeddings
        ... )
        >>> print(metrics)
        {'faithfulness': 0.95, 'answer_relevancy': 0.88}
    """
    evaluator = RAGASEvaluator(llm, embeddings)
    sample = EvaluationSample(
        query=query,
        contexts=contexts,
        answer=answer,
        ground_truth=ground_truth,
    )
    metrics = await evaluator.evaluate(sample)
    return metrics.to_dict()
