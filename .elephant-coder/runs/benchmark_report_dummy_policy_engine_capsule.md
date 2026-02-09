# Elephant Benchmark Report

- generated_at_utc: 2026-02-09T20:23:15Z
- benchmark_id: dummy_policy_engine_20260209T202214Z
- protocol_version: v1
- comparison_track: strategy
- tasks_total: 1
- runs_total: 2

## Aggregate
- token_reduction_pct: 28.84
- quality_delta_pct_points: 0.0
- latency_delta_ms: 578

## Mode Summary
| mode | runs | success_rate | avg_total_tokens | avg_latency_ms | total_cost_usd |
|---|---:|---:|---:|---:|---:|
| baseline | 1 | 100.0 | 3384 | 9001 | 0.00035 |
| elephant | 1 | 100.0 | 2408 | 9579 | 0.000276 |

## Per-Task Runs
| task_id | mode | success | total_tokens | latency_ms | cost_usd | retries | selected_model |
|---|---|---|---:|---:|---:|---:|---|
| policy_summary_01 | baseline | True | 3384 | 9001 | 0.000350 | 0 | qwen/qwen3-coder-next |
| policy_summary_01 | elephant | True | 2408 | 9579 | 0.000276 | 0 | qwen/qwen3-coder-next |
