# Elephant Benchmark Report

- generated_at_utc: 2026-02-09T20:21:19Z
- benchmark_id: dummy_event_mesh_20260209T202042Z
- protocol_version: v1
- comparison_track: strategy
- tasks_total: 1
- runs_total: 2

## Aggregate
- token_reduction_pct: 30.87
- quality_delta_pct_points: 0.0
- latency_delta_ms: -2295

## Mode Summary
| mode | runs | success_rate | avg_total_tokens | avg_latency_ms | total_cost_usd |
|---|---:|---:|---:|---:|---:|
| baseline | 1 | 100.0 | 3353 | 11287 | 0.000343 |
| elephant | 1 | 100.0 | 2318 | 8992 | 0.000251 |

## Per-Task Runs
| task_id | mode | success | total_tokens | latency_ms | cost_usd | retries | selected_model |
|---|---|---|---:|---:|---:|---:|---|
| event_summary_01 | baseline | True | 3353 | 11287 | 0.000343 | 0 | qwen/qwen3-coder-next |
| event_summary_01 | elephant | True | 2318 | 8992 | 0.000251 | 0 | qwen/qwen3-coder-next |
