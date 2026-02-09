# Elephant Benchmark Report

- generated_at_utc: 2026-02-09T20:23:30Z
- benchmark_id: dummy_layered_inheritance_20260209T202214Z
- protocol_version: v1
- comparison_track: strategy
- tasks_total: 1
- runs_total: 2

## Aggregate
- token_reduction_pct: 28.88
- quality_delta_pct_points: 0.0
- latency_delta_ms: 154

## Mode Summary
| mode | runs | success_rate | avg_total_tokens | avg_latency_ms | total_cost_usd |
|---|---:|---:|---:|---:|---:|
| baseline | 1 | 100.0 | 4464 | 7118 | 0.001059 |
| elephant | 1 | 100.0 | 3175 | 7272 | 0.000312 |

## Per-Task Runs
| task_id | mode | success | total_tokens | latency_ms | cost_usd | retries | selected_model |
|---|---|---|---:|---:|---:|---:|---|
| layered_summary_01 | baseline | True | 4464 | 7118 | 0.001059 | 0 | qwen/qwen3-coder-next |
| layered_summary_01 | elephant | True | 3175 | 7272 | 0.000312 | 0 | qwen/qwen3-coder-next |
