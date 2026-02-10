"""Metrics and monitoring setup"""

from fastapi import FastAPI
from prometheus_client import Counter, Histogram, make_asgi_app
import logging

logger = logging.getLogger(__name__)

# Define metrics
request_count = Counter(
    'http_requests_total',
    'Total HTTP requests',
    ['method', 'endpoint', 'status']
)

request_duration = Histogram(
    'http_request_duration_seconds',
    'HTTP request duration in seconds',
    ['method', 'endpoint']
)

agent_invocations = Counter(
    'agent_invocations_total',
    'Total agent invocations',
    ['agent_type']
)

rag_queries = Counter(
    'rag_queries_total',
    'Total RAG queries',
    ['status']
)

token_usage = Counter(
    'llm_tokens_total',
    'Total LLM tokens used',
    ['model', 'type']
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
