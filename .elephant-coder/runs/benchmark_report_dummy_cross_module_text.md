# Elephant Benchmark Report

- generated_at_utc: 2026-02-09T20:22:14Z
- benchmark_id: dummy_cross_module_20260209T202042Z
- protocol_version: v1
- comparison_track: strategy
- tasks_total: 1
- runs_total: 2

## Aggregate
- token_reduction_pct: 13.96
- quality_delta_pct_points: 0.0
- latency_delta_ms: -1599

## Mode Summary
| mode | runs | success_rate | avg_total_tokens | avg_latency_ms | total_cost_usd |
|---|---:|---:|---:|---:|---:|
| baseline | 1 | 0.0 | 3516 | 6995 | 0.000335 |
| elephant | 1 | 0.0 | 3025 | 5396 | 0.000723 |

## Per-Task Runs
| task_id | mode | success | total_tokens | latency_ms | cost_usd | retries | selected_model |
|---|---|---|---:|---:|---:|---:|---|
| cross_summary_01 | baseline | False | 3516 | 6995 | 0.000335 | 0 | qwen/qwen3-coder-next |
| cross_summary_01 | elephant | False | 3025 | 5396 | 0.000723 | 0 | qwen/qwen3-coder-next |
