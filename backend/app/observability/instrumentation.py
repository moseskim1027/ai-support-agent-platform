"""
Instrumentation helpers for recording metrics

This module provides convenient functions for instrumenting RAG pipelines
with Prometheus metrics and RAGAS evaluation.
"""

import logging
import time
from contextlib import contextmanager
from typing import Dict, Optional

from app.config import settings
from app.evaluation import RAGASMetrics
from app.observability import metrics

logger = logging.getLogger(__name__)


@contextmanager
def track_duration(histogram, labels: Optional[Dict[str, str]] = None):
    """
    Context manager to track operation duration

    Usage:
        with track_duration(metrics.rag_retrieval_duration, {"model": "gpt-4"}):
            # perform retrieval
            pass
    """
    start_time = time.time()
    try:
        yield
    finally:
        duration = time.time() - start_time
        if labels:
            histogram.labels(**labels).observe(duration)
        else:
            histogram.observe(duration)


class RAGMetricsRecorder:
    """
    Helper class for recording RAG-related metrics

    This class provides a clean interface for recording all RAG metrics
    including RAGAS scores, latency, tokens, and retrieval effectiveness.
    """

    def __init__(
        self,
        model_name: str = "unknown",
        environment: Optional[str] = None,
    ):
        """
        Initialize metrics recorder

        Args:
            model_name: Name of the model being used (e.g., "gemini-2.5-flash-lite")
            environment: Environment name (e.g., "production", "staging")
        """
        self.model_name = model_name
        self.environment = environment or settings.environment

    def record_retrieval_metrics(
        self,
        duration: float,
        num_contexts: int,
        avg_similarity: float,
        retrieval_method: str = "hybrid",
        success: bool = True,
    ):
        """
        Record retrieval stage metrics

        Args:
            duration: Retrieval duration in seconds
            num_contexts: Number of contexts retrieved
            avg_similarity: Average similarity score of retrieved contexts
            retrieval_method: Method used (dense, sparse, hybrid)
            success: Whether retrieval was successful
        """
        # Duration
        metrics.rag_retrieval_duration.labels(model=self.model_name).observe(duration)

        # Number of contexts
        metrics.retrieval_contexts_count.labels(model=self.model_name).observe(num_contexts)

        # Similarity score
        metrics.retrieval_similarity_score.labels(
            model=self.model_name,
            retrieval_method=retrieval_method,
        ).set(avg_similarity)

        # Hit/miss tracking
        status = "hit" if success and num_contexts > 0 else "miss"
        metrics.retrieval_hit_rate.labels(
            model=self.model_name,
            status=status,
        ).inc()

    def record_generation_metrics(
        self,
        duration: float,
        prompt_tokens: int,
        completion_tokens: int,
    ):
        """
        Record answer generation metrics

        Args:
            duration: Generation duration in seconds
            prompt_tokens: Number of tokens in prompt
            completion_tokens: Number of tokens in completion
        """
        # Duration
        metrics.rag_generation_duration.labels(model=self.model_name).observe(duration)

        # Token counts
        total_tokens = prompt_tokens + completion_tokens

        metrics.token_usage.labels(model=self.model_name, type="prompt").inc(prompt_tokens)
        metrics.token_usage.labels(model=self.model_name, type="completion").inc(completion_tokens)
        metrics.token_usage.labels(model=self.model_name, type="total").inc(total_tokens)

        # Token distributions
        metrics.token_usage_per_request.labels(model=self.model_name, type="prompt").observe(
            prompt_tokens
        )
        metrics.token_usage_per_request.labels(model=self.model_name, type="completion").observe(
            completion_tokens
        )
        metrics.token_usage_per_request.labels(model=self.model_name, type="total").observe(
            total_tokens
        )

    def record_ragas_metrics(
        self,
        ragas_metrics: RAGASMetrics,
        evaluation_duration: float,
    ):
        """
        Record RAGAS evaluation metrics

        Args:
            ragas_metrics: Computed RAGAS metrics
            evaluation_duration: Time taken to compute metrics
        """
        # Evaluation duration
        metrics.rag_evaluation_duration.observe(evaluation_duration)

        labels = {"model": self.model_name, "environment": self.environment}

        # Record each metric
        if ragas_metrics.faithfulness is not None:
            metrics.ragas_faithfulness.labels(**labels).set(ragas_metrics.faithfulness)
            metrics.ragas_metrics_histogram.labels(
                metric_name="faithfulness",
                model=self.model_name,
            ).observe(ragas_metrics.faithfulness)

        if ragas_metrics.answer_relevancy is not None:
            metrics.ragas_answer_relevancy.labels(**labels).set(ragas_metrics.answer_relevancy)
            metrics.ragas_metrics_histogram.labels(
                metric_name="answer_relevancy",
                model=self.model_name,
            ).observe(ragas_metrics.answer_relevancy)

        if ragas_metrics.context_precision is not None:
            metrics.ragas_context_precision.labels(**labels).set(ragas_metrics.context_precision)
            metrics.ragas_metrics_histogram.labels(
                metric_name="context_precision",
                model=self.model_name,
            ).observe(ragas_metrics.context_precision)

        if ragas_metrics.context_recall is not None:
            metrics.ragas_context_recall.labels(**labels).set(ragas_metrics.context_recall)
            metrics.ragas_metrics_histogram.labels(
                metric_name="context_recall",
                model=self.model_name,
            ).observe(ragas_metrics.context_recall)

    def record_total_duration(self, duration: float):
        """
        Record total end-to-end request duration

        Args:
            duration: Total duration in seconds
        """
        metrics.rag_total_duration.labels(model=self.model_name).observe(duration)

    def record_request_status(
        self,
        success: bool,
        error_type: Optional[str] = None,
    ):
        """
        Record request success/failure status

        Args:
            success: Whether the request succeeded
            error_type: Type of error if failed (retrieval, generation, evaluation)
        """
        status = "success" if success else "failure"
        error_type = error_type or "none"

        metrics.rag_request_status.labels(
            status=status,
            error_type=error_type,
        ).inc()

        metrics.rag_queries.labels(
            status=status,
            model=self.model_name,
            environment=self.environment,
        ).inc()


# Convenience function for full RAG request tracking
@contextmanager
def track_rag_request(model_name: str = "unknown"):
    """
    Context manager for tracking full RAG request

    Usage:
        with track_rag_request("gemini-2.5-flash-lite") as recorder:
            # Perform RAG operations
            recorder.record_retrieval_metrics(...)
            recorder.record_generation_metrics(...)
            recorder.record_ragas_metrics(...)

    Returns:
        RAGMetricsRecorder instance for recording metrics
    """
    recorder = RAGMetricsRecorder(model_name=model_name)
    start_time = time.time()
    success = True
    error_type = None

    try:
        yield recorder
    except Exception as e:
        success = False
        error_type = type(e).__name__
        raise
    finally:
        total_duration = time.time() - start_time
        recorder.record_total_duration(total_duration)
        recorder.record_request_status(success=success, error_type=error_type)
