# RAGAS-Based RAG Evaluation & Monitoring

This module implements RAGAS (Retrieval-Augmented Generation Assessment) metrics for evaluating and monitoring RAG system performance.

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    RAG Request Flow                         │
└─────────────────────────────────────────────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────────┐
│  1. Retrieval Stage                                         │
│     ├─ Fetch contexts from Qdrant                           │
│     ├─ Compute similarity scores                            │
│     └─ Record: duration, count, avg_similarity              │
└─────────────────────────────────────────────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────────┐
│  2. Generation Stage                                        │
│     ├─ Generate answer with LLM                             │
│     ├─ Track token usage (prompt + completion)              │
│     └─ Record: duration, tokens                             │
└─────────────────────────────────────────────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────────┐
│  3. RAGAS Evaluation Stage                                  │
│     ├─ Compute faithfulness (answer grounded in context)    │
│     ├─ Compute answer relevancy (relevance to query)        │
│     ├─ Compute context precision (if ground truth)          │
│     ├─ Compute context recall (if ground truth)             │
│     └─ Record: all RAGAS scores, evaluation duration        │
└─────────────────────────────────────────────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────────┐
│  4. Prometheus Export                                       │
│     ├─ RAGAS metrics (Gauges)                               │
│     ├─ Latency metrics (Histograms)                         │
│     ├─ Token consumption (Counters/Histograms)              │
│     ├─ Success/failure status (Counters)                    │
│     └─ Retrieval effectiveness (Gauges/Counters)            │
└─────────────────────────────────────────────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────────┐
│  5. Grafana Visualization                                   │
│     ├─ Real-time dashboards                                 │
│     ├─ Trend analysis                                       │
│     └─ Alert triggers                                       │
└─────────────────────────────────────────────────────────────┘
```

## Components

### 1. RAGAS Metrics Module (`ragas_metrics.py`)

Core evaluation engine computing RAGAS metrics.

**Key Classes:**
- `EvaluationSample`: Container for query, contexts, answer, and ground truth
- `RAGASMetrics`: Container for computed metric scores
- `RAGASEvaluator`: Main evaluator class

**Metrics Computed:**

| Metric | Description | Range | Requires Ground Truth |
|--------|-------------|-------|----------------------|
| Faithfulness | Answer is factually grounded in retrieved context | 0-1 | No |
| Answer Relevancy | Answer relevance to the user's query | 0-1 | No |
| Context Precision | Precision of retrieved contexts | 0-1 | Yes |
| Context Recall | Recall of retrieved contexts | 0-1 | Yes |

### 2. Prometheus Metrics (`observability/metrics.py`)

Extended Prometheus metrics for comprehensive RAG monitoring.

**Metric Categories:**
- **Latency**: Request duration, retrieval time, generation time, evaluation time
- **Token Usage**: Prompt tokens, completion tokens, total tokens (counters & histograms)
- **RAGAS Scores**: All RAGAS metrics as gauges
- **Retrieval**: Hit rate, similarity scores, context counts
- **Status**: Success/failure rates with error classification

### 3. Instrumentation (`observability/instrumentation.py`)

Helper utilities for recording metrics in RAG pipelines.

**Key Classes:**
- `RAGMetricsRecorder`: Convenient interface for recording all metrics
- `track_rag_request`: Context manager for full request tracking

## Usage Examples

### Basic Usage

```python
from app.evaluation import RAGASEvaluator, EvaluationSample

# Initialize evaluator
evaluator = RAGASEvaluator(llm=my_llm, embeddings=my_embeddings)

# Create sample
sample = EvaluationSample(
    query="What is your return policy?",
    contexts=[
        "We accept returns within 30 days of purchase.",
        "Items must be in original condition with tags attached."
    ],
    answer="You can return items within 30 days if they're in original condition."
)

# Evaluate
metrics = await evaluator.evaluate(sample)
print(metrics.to_dict())
# Output: {'faithfulness': 0.95, 'answer_relevancy': 0.88}
```

### Integration with RAG Agent

```python
from app.observability import track_rag_request
from app.evaluation import EvaluationSample, RAGASEvaluator
import time

async def process_rag_query(query: str):
    # Initialize tracking
    with track_rag_request(model_name="gemini-2.5-flash-lite") as recorder:

        # 1. Retrieval stage
        retrieval_start = time.time()
        contexts = await retrieve_contexts(query)
        retrieval_duration = time.time() - retrieval_start

        recorder.record_retrieval_metrics(
            duration=retrieval_duration,
            num_contexts=len(contexts),
            avg_similarity=compute_avg_similarity(contexts),
            retrieval_method="hybrid",
            success=True
        )

        # 2. Generation stage
        generation_start = time.time()
        answer, token_info = await generate_answer(query, contexts)
        generation_duration = time.time() - generation_start

        recorder.record_generation_metrics(
            duration=generation_duration,
            prompt_tokens=token_info['prompt_tokens'],
            completion_tokens=token_info['completion_tokens']
        )

        # 3. RAGAS evaluation
        evaluation_start = time.time()
        evaluator = RAGASEvaluator(llm=my_llm, embeddings=my_embeddings)
        sample = EvaluationSample(
            query=query,
            contexts=[c['text'] for c in contexts],
            answer=answer
        )
        ragas_metrics = await evaluator.evaluate(sample)
        evaluation_duration = time.time() - evaluation_start

        recorder.record_ragas_metrics(
            ragas_metrics=ragas_metrics,
            evaluation_duration=evaluation_duration
        )

        return answer, ragas_metrics
```

### Batch Evaluation

```python
# Evaluate multiple samples
samples = [
    EvaluationSample(query=q, contexts=c, answer=a)
    for q, c, a in zip(queries, contexts_list, answers)
]

results = await evaluator.evaluate_batch(samples)

# Analyze results
avg_faithfulness = sum(m.faithfulness for m in results) / len(results)
print(f"Average faithfulness: {avg_faithfulness:.2f}")
```

## Prometheus Metrics Reference

### RAGAS Metrics (Gauges)

```
ragas_faithfulness_score{model="...", environment="..."}
ragas_answer_relevancy_score{model="...", environment="..."}
ragas_context_precision_score{model="...", environment="..."}
ragas_context_recall_score{model="...", environment="..."}
```

### Latency Metrics (Histograms)

```
rag_total_duration_seconds{model="..."}
rag_retrieval_duration_seconds{model="..."}
rag_generation_duration_seconds{model="..."}
rag_evaluation_duration_seconds
```

### Token Metrics

```
llm_tokens_total{model="...", type="prompt|completion|total"}
llm_tokens_per_request{model="...", type="..."}
```

### Retrieval Metrics

```
rag_retrieval_contexts_count{model="..."}
rag_retrieval_avg_similarity{model="...", retrieval_method="..."}
rag_retrieval_hits_total{model="...", status="hit|miss"}
```

### Status Metrics

```
rag_request_status_total{status="success|failure", error_type="..."}
rag_queries_total{status="...", model="...", environment="..."}
```

## Grafana Dashboard

A pre-configured Grafana dashboard is available at:
`infrastructure/grafana/dashboards/rag-monitoring.json`

**Dashboard Panels:**
1. Request Latency (P50, P95, P99)
2. Token Consumption Over Time
3. Success vs Failure Rate
4. RAGAS Faithfulness Score
5. RAGAS Answer Relevancy
6. Retrieval Hit Rate
7. Average Retrieval Similarity
8. Pipeline Stage Latency
9. RAGAS Metrics Distribution

**To Import:**
1. Open Grafana
2. Go to Dashboards → Import
3. Upload `rag-monitoring.json`
4. Select your Prometheus data source

## Prometheus Query Examples

See `infrastructure/grafana/PROMETHEUS_QUERIES.md` for comprehensive query examples.

**Quick Examples:**

```promql
# P95 latency
histogram_quantile(0.95, sum(rate(rag_total_duration_seconds_bucket[5m])) by (le, model))

# Token usage rate
rate(llm_tokens_total{type="total"}[5m])

# Success rate percentage
sum(rate(rag_request_status_total{status="success"}[5m])) /
sum(rate(rag_request_status_total[5m])) * 100

# Current faithfulness score
ragas_faithfulness_score
```

## Configuration

### Environment Variables

```bash
# Required
GEMINI_API_KEY=your_api_key_here

# Optional
ENVIRONMENT=production  # Used for metric labeling
ENABLE_RAGAS_EVALUATION=true  # Enable/disable RAGAS (default: true)
```

### Assumptions

1. **LLM Access**: RAGAS evaluation requires an LLM (configured in `RAGASEvaluator`)
2. **Embeddings**: Embedding model needed for similarity calculations
3. **Async Context**: All evaluation methods are async
4. **Error Handling**: Evaluation failures don't crash the pipeline; they return empty metrics
5. **Performance**: RAGAS evaluation adds ~1-5s latency per request (monitored separately)

## Extending the System

### Adding Custom Metrics

```python
# 1. Define metric in metrics.py
from prometheus_client import Gauge

custom_metric = Gauge(
    "rag_custom_metric",
    "Description of custom metric",
    ["label1", "label2"]
)

# 2. Record in instrumentation.py
def record_custom_metric(self, value: float):
    custom_metric.labels(
        label1=self.model_name,
        label2="value"
    ).set(value)

# 3. Use in RAG agent
recorder.record_custom_metric(my_value)
```

### Adding RAGAS Metrics

```python
# Import new RAGAS metric
from ragas.metrics import context_entity_recall

# Add to evaluator
class RAGASEvaluator:
    def __init__(self, ...):
        self.metrics_with_ground_truth = [
            faithfulness,
            answer_relevancy,
            context_precision,
            context_recall,
            context_entity_recall,  # New metric
        ]
```

## Performance Considerations

1. **RAGAS Overhead**: Adds 1-5s per request (async, non-blocking)
2. **Metrics Storage**: ~50 metric series per model/environment
3. **Memory**: Minimal impact (<100MB for RAGAS module)
4. **Prometheus**: Configure retention based on query volume

## Troubleshooting

### RAGAS Evaluation Fails

```python
# Check logs for errors
logger.error(f"RAGAS evaluation failed: {error}")

# Metrics will be empty but request succeeds
ragas_metrics = RAGASMetrics()  # All None
```

### Missing Prometheus Metrics

```bash
# Verify metrics endpoint
curl http://localhost:8000/metrics | grep ragas

# Check Prometheus scrape config
- job_name: 'backend'
  static_configs:
    - targets: ['backend:8000']
```

### Low RAGAS Scores

- **Faithfulness < 0.7**: Answer may contain hallucinations
- **Relevancy < 0.7**: Answer may not address the query
- **Precision < 0.5**: Retrieved contexts contain noise
- **Recall < 0.5**: Missing relevant contexts

## References

- [RAGAS Documentation](https://docs.ragas.io/)
- [Prometheus Best Practices](https://prometheus.io/docs/practices/)
- [Grafana Dashboard Guide](https://grafana.com/docs/grafana/latest/dashboards/)
