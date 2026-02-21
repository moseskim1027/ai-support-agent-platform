# Prometheus Queries for RAG Monitoring

This document provides example Prometheus queries for monitoring RAG system performance with RAGAS metrics.

## Latency Metrics

### Request Latency Percentiles

```promql
# P50 (Median)
histogram_quantile(0.50, sum(rate(rag_total_duration_seconds_bucket[5m])) by (le, model))

# P95
histogram_quantile(0.95, sum(rate(rag_total_duration_seconds_bucket[5m])) by (le, model))

# P99
histogram_quantile(0.99, sum(rate(rag_total_duration_seconds_bucket[5m])) by (le, model))
```

### Pipeline Stage Latency

```promql
# Retrieval latency (P95)
histogram_quantile(0.95, sum(rate(rag_retrieval_duration_seconds_bucket[5m])) by (le, model))

# Generation latency (P95)
histogram_quantile(0.95, sum(rate(rag_generation_duration_seconds_bucket[5m])) by (le, model))

# Evaluation latency (P95)
histogram_quantile(0.95, sum(rate(rag_evaluation_duration_seconds_bucket[5m])) by (le))
```

### Average Latency

```promql
# Average total latency over 5 minutes
rate(rag_total_duration_seconds_sum[5m]) / rate(rag_total_duration_seconds_count[5m])
```

## Token Consumption

### Token Usage Rate

```promql
# Total tokens per second
rate(llm_tokens_total{type="total"}[5m])

# Prompt tokens per second
rate(llm_tokens_total{type="prompt"}[5m])

# Completion tokens per second
rate(llm_tokens_total{type="completion"}[5m])
```

### Cumulative Token Usage

```promql
# Total tokens used (all time)
llm_tokens_total{type="total"}

# By model
sum(llm_tokens_total{type="total"}) by (model)
```

### Average Tokens Per Request

```promql
# Average prompt tokens per request
rate(llm_tokens_total{type="prompt"}[5m]) / rate(rag_queries_total[5m])

# Average completion tokens per request
rate(llm_tokens_total{type="completion"}[5m]) / rate(rag_queries_total[5m])
```

### Token Distribution

```promql
# P95 token usage per request
histogram_quantile(0.95, sum(rate(llm_tokens_per_request_bucket{type="total"}[5m])) by (le, model))
```

## Success vs Failure Rate

### Request Success Rate

```promql
# Success rate percentage
sum(rate(rag_request_status_total{status="success"}[5m])) /
sum(rate(rag_request_status_total[5m])) * 100

# Failure rate percentage
sum(rate(rag_request_status_total{status="failure"}[5m])) /
sum(rate(rag_request_status_total[5m])) * 100
```

### Failures by Error Type

```promql
# Count failures by error type
sum(rate(rag_request_status_total{status="failure"}[5m])) by (error_type)
```

### Query Success Over Time

```promql
# Successful queries per minute
sum(rate(rag_queries_total{status="success"}[1m])) * 60
```

## RAGAS Metrics

### Current RAGAS Scores

```promql
# Faithfulness score
ragas_faithfulness_score

# Answer relevancy score
ragas_answer_relevancy_score

# Context precision score
ragas_context_precision_score

# Context recall score
ragas_context_recall_score
```

### RAGAS Metric Trends

```promql
# Average faithfulness over time
avg_over_time(ragas_faithfulness_score[1h])

# Minimum answer relevancy in last hour
min_over_time(ragas_answer_relevancy_score[1h])
```

### RAGAS Metrics by Model

```promql
# Faithfulness by model
ragas_faithfulness_score{model="gemini-2.5-flash-lite"}

# Answer relevancy by environment
ragas_answer_relevancy_score{environment="production"}
```

### RAGAS Metric Distribution

```promql
# Distribution of faithfulness scores
sum(rate(ragas_metric_scores_bucket{metric_name="faithfulness"}[5m])) by (le)
```

### Low Score Alerts

```promql
# Queries with faithfulness below 0.7
ragas_faithfulness_score < 0.7

# Queries with answer relevancy below 0.8
ragas_answer_relevancy_score < 0.8
```

## Retrieval Effectiveness

### Hit Rate

```promql
# Retrieval hit rate (percentage)
rate(rag_retrieval_hits_total{status="hit"}[5m]) /
(rate(rag_retrieval_hits_total{status="hit"}[5m]) +
 rate(rag_retrieval_hits_total{status="miss"}[5m])) * 100
```

### Average Similarity Score

```promql
# Current average similarity
rag_retrieval_avg_similarity

# By retrieval method
rag_retrieval_avg_similarity{retrieval_method="hybrid"}
```

### Context Count Statistics

```promql
# Average number of contexts retrieved
rate(rag_retrieval_contexts_count_sum[5m]) / rate(rag_retrieval_contexts_count_count[5m])

# P95 context count
histogram_quantile(0.95, sum(rate(rag_retrieval_contexts_count_bucket[5m])) by (le, model))
```

## Aggregations and Comparisons

### Model Comparison

```promql
# Compare latency across models
sum(rate(rag_total_duration_seconds_sum[5m])) by (model) /
sum(rate(rag_total_duration_seconds_count[5m])) by (model)

# Compare token usage across models
sum(rate(llm_tokens_total{type="total"}[5m])) by (model)

# Compare RAGAS scores across models
ragas_faithfulness_score or ragas_answer_relevancy_score
```

### Environment Comparison

```promql
# Production vs staging performance
ragas_faithfulness_score{environment="production"} or
ragas_faithfulness_score{environment="staging"}
```

### Time-based Analysis

```promql
# Queries per hour
sum(rate(rag_queries_total[1h])) * 3600

# Peak hour detection
topk(1, sum(rate(rag_queries_total[1h])) by (hour))
```

## Alerts (Example Thresholds)

### High Latency Alert

```promql
# Alert if P95 latency > 10 seconds
histogram_quantile(0.95, sum(rate(rag_total_duration_seconds_bucket[5m])) by (le)) > 10
```

### Low RAGAS Score Alert

```promql
# Alert if faithfulness drops below 0.7
ragas_faithfulness_score < 0.7

# Alert if answer relevancy drops below 0.75
ragas_answer_relevancy_score < 0.75
```

### High Failure Rate Alert

```promql
# Alert if failure rate > 5%
(sum(rate(rag_request_status_total{status="failure"}[5m])) /
 sum(rate(rag_request_status_total[5m]))) > 0.05
```

### Token Budget Alert

```promql
# Alert if token usage > 1M tokens per hour
rate(llm_tokens_total{type="total"}[1h]) * 3600 > 1000000
```

## Dashboard Panel Examples

### Single Stat Panels

```promql
# Current success rate
sum(rate(rag_request_status_total{status="success"}[5m])) /
sum(rate(rag_request_status_total[5m])) * 100

# Average RAGAS score (all metrics)
avg(ragas_faithfulness_score or ragas_answer_relevancy_score)

# Requests per minute
sum(rate(rag_queries_total[1m])) * 60
```

### Gauge Panels

```promql
# Current P95 latency
histogram_quantile(0.95, sum(rate(rag_total_duration_seconds_bucket[5m])) by (le))

# Current faithfulness score
ragas_faithfulness_score
```

### Heatmap Panels

```promql
# Latency distribution heatmap
sum(rate(rag_total_duration_seconds_bucket[5m])) by (le)

# RAGAS metric distribution heatmap
sum(rate(ragas_metric_scores_bucket[5m])) by (le, metric_name)
```

## Notes

- All rate queries use `[5m]` windows by default. Adjust based on your traffic patterns.
- Use longer windows (`[1h]`, `[24h]`) for trend analysis.
- Combine queries with logical operators (`and`, `or`, `unless`) for complex conditions.
- Use `by` clause to group metrics by labels (model, environment, etc.).
- Use aggregation functions: `sum`, `avg`, `min`, `max`, `count`.
- For percentiles, always use `histogram_quantile` with bucket metrics.
