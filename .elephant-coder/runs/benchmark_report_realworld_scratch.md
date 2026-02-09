# Elephant Benchmark Report

- generated_at_utc: 2026-02-09T18:32:24Z
- benchmark_id: realworld_scratch_20260209T183119Z
- protocol_version: v1
- comparison_track: strategy
- tasks_total: 3
- runs_total: 6

## Aggregate
- token_reduction_pct: -33.19
- quality_delta_pct_points: 0.0
- latency_delta_ms: 1542

## Mode Summary
| mode | runs | success_rate | avg_total_tokens | avg_latency_ms | total_cost_usd |
|---|---:|---:|---:|---:|---:|
| baseline | 3 | 100.0 | 717 | 2465 | 0.000287 |
| elephant | 3 | 100.0 | 955 | 4007 | 0.000459 |

## Per-Task Runs
| task_id | mode | success | total_tokens | latency_ms | cost_usd | retries | selected_model |
|---|---|---|---:|---:|---:|---:|---|
| scratch_python_01 | baseline | True | 709 | 3430 | 0.000117 | 0 | qwen/qwen3-coder-next |
| scratch_python_01 | elephant | True | 1018 | 3985 | 0.000150 | 0 | qwen/qwen3-coder-next |
| scratch_readme_02 | baseline | True | 774 | 2167 | 0.000102 | 0 | qwen/qwen3-coder-next |
| scratch_readme_02 | elephant | True | 893 | 6561 | 0.000105 | 0 | qwen/qwen3-coder-next |
| scratch_cli_03 | baseline | True | 669 | 1798 | 0.000069 | 0 | qwen/qwen3-coder-next |
| scratch_cli_03 | elephant | True | 955 | 1476 | 0.000204 | 0 | qwen/qwen3-coder-next |
