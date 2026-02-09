# Elephant Benchmark Report

- generated_at_utc: 2026-02-09T20:37:56Z
- benchmark_id: dummy_policy_engine_20260209T203040Z
- protocol_version: v1
- comparison_track: strategy
- tasks_total: 4
- runs_total: 8

## Aggregate
- token_reduction_pct: 21.73
- quality_delta_pct_points: 0.0
- latency_delta_ms: -4037

## Mode Summary
| mode | runs | success_rate | avg_total_tokens | avg_latency_ms | total_cost_usd |
|---|---:|---:|---:|---:|---:|
| baseline | 4 | 25.0 | 3506 | 16641 | 0.002607 |
| elephant | 4 | 25.0 | 2744 | 12604 | 0.002371 |

## Per-Task Runs
| task_id | mode | success | total_tokens | latency_ms | cost_usd | retries | selected_model |
|---|---|---|---:|---:|---:|---:|---|
| policy_summary_01 | baseline | True | 3352 | 23268 | 0.000341 | 0 | qwen/qwen3-coder-next |
| policy_summary_01 | elephant | True | 2365 | 15634 | 0.000263 | 0 | qwen/qwen3-coder-next |
| policy_feature_02 | baseline | False | 3653 | 22741 | 0.000419 | 0 | qwen/qwen3-coder-next |
| policy_feature_02 | elephant | False | 2824 | 9732 | 0.000900 | 0 | qwen/qwen3-coder-next |
| policy_feature_03 | baseline | False | 3344 | 15834 | 0.000332 | 0 | qwen/qwen3-coder-next |
| policy_feature_03 | elephant | False | 2698 | 15749 | 0.000280 | 0 | qwen/qwen3-coder-next |
| policy_invariant_04 | baseline | False | 3675 | 4722 | 0.001515 | 0 | qwen/qwen3-coder-next |
| policy_invariant_04 | elephant | False | 3091 | 9304 | 0.000928 | 0 | qwen/qwen3-coder-next |
