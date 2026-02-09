# Elephant Benchmark Report

- generated_at_utc: 2026-02-09T20:20:58Z
- benchmark_id: dummy_oop_20260209T202042Z
- protocol_version: v1
- comparison_track: strategy
- tasks_total: 1
- runs_total: 2

## Aggregate
- token_reduction_pct: 36.18
- quality_delta_pct_points: 0.0
- latency_delta_ms: 5182

## Mode Summary
| mode | runs | success_rate | avg_total_tokens | avg_latency_ms | total_cost_usd |
|---|---:|---:|---:|---:|---:|
| baseline | 1 | 100.0 | 5774 | 5017 | 0.001279 |
| elephant | 1 | 100.0 | 3685 | 10199 | 0.000362 |

## Per-Task Runs
| task_id | mode | success | total_tokens | latency_ms | cost_usd | retries | selected_model |
|---|---|---|---:|---:|---:|---:|---|
| dummy_summary_01 | baseline | True | 5774 | 5017 | 0.001279 | 0 | qwen/qwen3-coder-next |
| dummy_summary_01 | elephant | True | 3685 | 10199 | 0.000362 | 0 | qwen/qwen3-coder-next |
