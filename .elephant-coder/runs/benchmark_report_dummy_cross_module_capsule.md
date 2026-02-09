# Elephant Benchmark Report

- generated_at_utc: 2026-02-09T20:23:44Z
- benchmark_id: dummy_cross_module_20260209T202214Z
- protocol_version: v1
- comparison_track: strategy
- tasks_total: 1
- runs_total: 2

## Aggregate
- token_reduction_pct: 15.68
- quality_delta_pct_points: 100.0
- latency_delta_ms: -4369

## Mode Summary
| mode | runs | success_rate | avg_total_tokens | avg_latency_ms | total_cost_usd |
|---|---:|---:|---:|---:|---:|
| baseline | 1 | 0.0 | 3534 | 8500 | 0.00034 |
| elephant | 1 | 100.0 | 2980 | 4131 | 0.000688 |

## Per-Task Runs
| task_id | mode | success | total_tokens | latency_ms | cost_usd | retries | selected_model |
|---|---|---|---:|---:|---:|---:|---|
| cross_summary_01 | baseline | False | 3534 | 8500 | 0.000340 | 0 | qwen/qwen3-coder-next |
| cross_summary_01 | elephant | True | 2980 | 4131 | 0.000688 | 0 | qwen/qwen3-coder-next |
