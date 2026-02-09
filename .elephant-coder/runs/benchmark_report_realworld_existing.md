# Elephant Benchmark Report

- generated_at_utc: 2026-02-09T18:31:59Z
- benchmark_id: realworld_existing_20260209T183119Z
- protocol_version: v1
- comparison_track: strategy
- tasks_total: 3
- runs_total: 6

## Aggregate
- token_reduction_pct: 79.02
- quality_delta_pct_points: 33.33
- latency_delta_ms: 408

## Mode Summary
| mode | runs | success_rate | avg_total_tokens | avg_latency_ms | total_cost_usd |
|---|---:|---:|---:|---:|---:|
| baseline | 3 | 66.67 | 18340 | 5975 | 0.004083 |
| elephant | 3 | 100.0 | 3847 | 6383 | 0.003724 |

## Per-Task Runs
| task_id | mode | success | total_tokens | latency_ms | cost_usd | retries | selected_model |
|---|---|---|---:|---:|---:|---:|---|
| existing_docs_01 | baseline | False | 18108 | 4188 | 0.001312 | 0 | qwen/qwen3-coder-next |
| existing_docs_01 | elephant | True | 3505 | 3568 | 0.001025 | 0 | qwen/qwen3-coder-next |
| existing_script_02 | baseline | True | 18365 | 5348 | 0.001380 | 0 | qwen/qwen3-coder-next |
| existing_script_02 | elephant | True | 3986 | 10417 | 0.002317 | 0 | qwen/qwen3-coder-next |
| existing_module_03 | baseline | True | 18548 | 8390 | 0.001391 | 0 | qwen/qwen3-coder-next |
| existing_module_03 | elephant | True | 4050 | 5164 | 0.000381 | 0 | qwen/qwen3-coder-next |
