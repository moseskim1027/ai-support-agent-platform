"""Metrics and monitoring setup"""

import logging

from fastapi import FastAPI
from prometheus_client import Counter, Gauge, Histogram, make_asgi_app

logger = logging.getLogger(__name__)

# ========================================
# HTTP & General Metrics
# ========================================

request_count = Counter(
    "http_requests_total", "Total HTTP requests", ["method", "endpoint", "status"]
)

request_duration = Histogram(
    "http_request_duration_seconds",
    "HTTP request duration in seconds",
    ["method", "endpoint"],
    buckets=(0.005, 0.01, 0.025, 0.05, 0.075, 0.1, 0.25, 0.5, 0.75, 1.0, 2.5, 5.0, 7.5, 10.0),
)

agent_invocations = Counter("agent_invocations_total", "Total agent invocations", ["agent_type"])

# ========================================
# RAG-Specific Metrics
# ========================================

rag_queries = Counter(
    "rag_queries_total",
    "Total RAG queries",
    ["status", "model", "environment"],
)

# Latency metrics for RAG pipeline stages
rag_retrieval_duration = Histogram(
    "rag_retrieval_duration_seconds",
    "Duration of context retrieval in seconds",
    ["model"],
    buckets=(0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1.0, 2.5, 5.0),
)

rag_generation_duration = Histogram(
    "rag_generation_duration_seconds",
    "Duration of answer generation in seconds",
    ["model"],
    buckets=(0.1, 0.25, 0.5, 1.0, 2.5, 5.0, 7.5, 10.0, 15.0),
)

rag_evaluation_duration = Histogram(
    "rag_evaluation_duration_seconds",
    "Duration of RAGAS metric computation in seconds",
    buckets=(0.5, 1.0, 2.5, 5.0, 10.0, 15.0, 30.0),
)

rag_total_duration = Histogram(
    "rag_total_duration_seconds",
    "Total end-to-end RAG query duration in seconds",
    ["model"],
    buckets=(0.5, 1.0, 2.5, 5.0, 7.5, 10.0, 15.0, 20.0, 30.0),
)

# ========================================
# Token Usage Metrics
# ========================================

token_usage = Counter(
    "llm_tokens_total",
    "Total LLM tokens used",
    ["model", "type"],  # type: prompt, completion, or total
)

token_usage_per_request = Histogram(
    "llm_tokens_per_request",
    "Token usage per request",
    ["model", "type"],
    buckets=(10, 50, 100, 250, 500, 1000, 2500, 5000, 10000),
)

# ========================================
# RAGAS Evaluation Metrics
# ========================================

ragas_faithfulness = Gauge(
    "ragas_faithfulness_score",
    "RAGAS faithfulness score (0-1)",
    ["model", "environment"],
)

ragas_answer_relevancy = Gauge(
    "ragas_answer_relevancy_score",
    "RAGAS answer relevancy score (0-1)",
    ["model", "environment"],
)

ragas_context_precision = Gauge(
    "ragas_context_precision_score",
    "RAGAS context precision score (0-1)",
    ["model", "environment"],
)

ragas_context_recall = Gauge(
    "ragas_context_recall_score",
    "RAGAS context recall score (0-1)",
    ["model", "environment"],
)

# Histogram for tracking metric distributions
ragas_metrics_histogram = Histogram(
    "ragas_metric_scores",
    "Distribution of RAGAS metric scores",
    ["metric_name", "model"],
    buckets=(0.0, 0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9, 1.0),
)

# ========================================
# Retrieval Effectiveness Metrics
# ========================================

retrieval_contexts_count = Histogram(
    "rag_retrieval_contexts_count",
    "Number of contexts retrieved per query",
    ["model"],
    buckets=(1, 2, 3, 5, 10, 20, 50),
)

retrieval_similarity_score = Gauge(
    "rag_retrieval_avg_similarity",
    "Average similarity score of retrieved contexts",
    ["model", "retrieval_method"],  # retrieval_method: dense, sparse, hybrid
)

retrieval_hit_rate = Counter(
    "rag_retrieval_hits_total",
    "Number of successful retrievals (found relevant context)",
    ["model", "status"],  # status: hit, miss
)

# ========================================
# Success / Failure Tracking
# ========================================

rag_request_status = Counter(
    "rag_request_status_total",
    "RAG request outcomes",
    ["status", "error_type"],  # status: success, failure; error_type: retrieval, generation, evaluation
)


def setup_metrics(app: FastAPI):
    """
    Setup Prometheus metrics endpoint

    Args:
        app: FastAPI application instance
    """
    logger.info("Setting up Prometheus metrics...")

    # Mount prometheus metrics endpoint
    metrics_app = make_asgi_app()
    app.mount("/metrics", metrics_app)

    logger.info("Metrics endpoint available at /metrics")
