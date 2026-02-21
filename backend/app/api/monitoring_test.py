"""
Monitoring Test API Endpoints

Provides endpoints to generate test metrics for Prometheus/Grafana visualization.
"""

import asyncio
import random
import time

from fastapi import APIRouter, BackgroundTasks
from pydantic import BaseModel

from app.evaluation import RAGASMetrics
from app.observability.instrumentation import RAGMetricsRecorder

router = APIRouter(prefix="/test", tags=["monitoring-test"])


# ============================================================================
# Test Query Data
# ============================================================================


TEST_QUERIES = [
    ("What is your return policy?", "normal"),
    ("How do I track my order?", "high_quality"),
    ("Can I cancel my subscription?", "normal"),
    ("What payment methods do you accept?", "high_quality"),
    ("How long does shipping take?", "normal"),
    ("What are the features of the premium plan?", "high_quality"),
    ("Tell me about your pricing tiers", "normal"),
    ("Do you offer student discounts?", "low_quality"),
    ("What's included in the free trial?", "high_quality"),
    ("How do I reset my password?", "normal"),
]


# ============================================================================
# Simulation Logic
# ============================================================================


async def simulate_single_query(
    recorder: RAGMetricsRecorder, query: str, scenario: str
) -> RAGASMetrics:
    """Simulate a single RAG query"""

    # Retrieval stage
    await asyncio.sleep(random.uniform(0.1, 0.3))

    if scenario == "high_quality":
        num_contexts = random.randint(3, 5)
        avg_similarity = random.uniform(0.85, 0.95)
    elif scenario == "low_quality":
        num_contexts = random.randint(1, 2)
        avg_similarity = random.uniform(0.4, 0.6)
    else:
        num_contexts = random.randint(2, 4)
        avg_similarity = random.uniform(0.7, 0.85)

    recorder.record_retrieval_metrics(
        duration=random.uniform(0.1, 0.3),
        num_contexts=num_contexts,
        avg_similarity=avg_similarity,
        retrieval_method="hybrid",
        success=True,
    )

    # Generation stage
    await asyncio.sleep(random.uniform(0.5, 1.5))

    # Realistic token counts based on actual query metrics (~263 prompt, ~200 completion)
    if scenario == "high_quality":
        prompt_tokens = random.randint(250, 400)
        completion_tokens = random.randint(200, 300)
    elif scenario == "low_quality":
        prompt_tokens = random.randint(150, 250)
        completion_tokens = random.randint(100, 150)
    else:  # normal
        prompt_tokens = random.randint(200, 320)
        completion_tokens = random.randint(150, 250)

    recorder.record_generation_metrics(
        duration=random.uniform(0.5, 1.5),
        prompt_tokens=prompt_tokens,
        completion_tokens=completion_tokens,
    )

    # RAGAS evaluation
    await asyncio.sleep(random.uniform(1.0, 2.5))

    if scenario == "high_quality":
        ragas_metrics = RAGASMetrics(
            faithfulness=random.uniform(0.85, 0.95),
            answer_relevancy=random.uniform(0.88, 0.97),
            context_precision=random.uniform(0.80, 0.92),
            context_recall=random.uniform(0.82, 0.94),
        )
    elif scenario == "low_quality":
        ragas_metrics = RAGASMetrics(
            faithfulness=random.uniform(0.45, 0.65),
            answer_relevancy=random.uniform(0.50, 0.70),
            context_precision=random.uniform(0.40, 0.60),
            context_recall=random.uniform(0.35, 0.55),
        )
    else:
        ragas_metrics = RAGASMetrics(
            faithfulness=random.uniform(0.70, 0.85),
            answer_relevancy=random.uniform(0.75, 0.88),
            context_precision=random.uniform(0.65, 0.80),
            context_recall=random.uniform(0.68, 0.82),
        )

    recorder.record_ragas_metrics(
        ragas_metrics=ragas_metrics, evaluation_duration=random.uniform(1.0, 2.5)
    )

    return ragas_metrics


async def run_monitoring_simulation(
    num_queries: int = 10, model_name: str = "gemini-2.5-flash-lite"
):
    """Run monitoring simulation"""

    queries_to_run = TEST_QUERIES * ((num_queries // len(TEST_QUERIES)) + 1)
    queries_to_run = queries_to_run[:num_queries]

    for query, scenario in queries_to_run:
        recorder = RAGMetricsRecorder(model_name=model_name)
        start_time = time.time()

        try:
            await simulate_single_query(recorder, query, scenario)
            total_duration = time.time() - start_time
            recorder.record_total_duration(total_duration)
            recorder.record_request_status(success=True)
        except Exception:
            total_duration = time.time() - start_time
            recorder.record_total_duration(total_duration)
            recorder.record_request_status(success=False, error_type="test")

        # Small delay between queries
        await asyncio.sleep(0.2)


# ============================================================================
# API Endpoints
# ============================================================================


class SimulationRequest(BaseModel):
    """Request model for simulation"""

    num_queries: int = 20
    model_name: str = "gemini-2.5-flash-lite"


class SimulationResponse(BaseModel):
    """Response model for simulation"""

    status: str
    message: str
    num_queries: int


@router.post("/simulate-metrics", response_model=SimulationResponse)
async def simulate_metrics(request: SimulationRequest, background_tasks: BackgroundTasks):
    """
    Generate test metrics for monitoring dashboard

    This endpoint simulates RAG queries to populate Prometheus metrics
    and Grafana dashboards with realistic data.
    """

    # Run simulation in background
    background_tasks.add_task(run_monitoring_simulation, request.num_queries, request.model_name)

    return SimulationResponse(
        status="started",
        message=f"Simulation started with {request.num_queries} queries",
        num_queries=request.num_queries,
    )


@router.get("/simulate-metrics-sync")
async def simulate_metrics_sync(num_queries: int = 10):
    """
    Generate test metrics synchronously (blocks until complete)

    Use this for immediate metric generation. For large numbers of queries,
    use the POST endpoint which runs in the background.
    """

    await run_monitoring_simulation(num_queries=num_queries)

    return {
        "status": "complete",
        "message": f"Generated metrics for {num_queries} queries",
        "num_queries": num_queries,
        "metrics_url": "/metrics/",
    }
