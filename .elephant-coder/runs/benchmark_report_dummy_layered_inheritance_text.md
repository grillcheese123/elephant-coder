# Elephant Benchmark Report

- generated_at_utc: 2026-02-09T20:22:00Z
- benchmark_id: dummy_layered_inheritance_20260209T202042Z
- protocol_version: v1
- comparison_track: strategy
- tasks_total: 1
- runs_total: 2

## Aggregate
- token_reduction_pct: 22.77
- quality_delta_pct_points: 0.0
- latency_delta_ms: 6547

## Mode Summary
| mode | runs | success_rate | avg_total_tokens | avg_latency_ms | total_cost_usd |
|---|---:|---:|---:|---:|---:|
| baseline | 1 | 100.0 | 4264 | 3531 | 0.0009 |
| elephant | 1 | 100.0 | 3293 | 10078 | 0.000348 |

## Per-Task Runs
| task_id | mode | success | total_tokens | latency_ms | cost_usd | retries | selected_model |
|---|---|---|---:|---:|---:|---:|---|
| layered_summary_01 | baseline | True | 4264 | 3531 | 0.000900 | 0 | qwen/qwen3-coder-next |
| layered_summary_01 | elephant | True | 3293 | 10078 | 0.000348 | 0 | qwen/qwen3-coder-next |
