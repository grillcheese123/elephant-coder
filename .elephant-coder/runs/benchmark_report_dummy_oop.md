# Elephant Benchmark Report

- generated_at_utc: 2026-02-09T20:33:08Z
- benchmark_id: dummy_oop_20260209T203040Z
- protocol_version: v1
- comparison_track: strategy
- tasks_total: 4
- runs_total: 8

## Aggregate
- token_reduction_pct: 29.48
- quality_delta_pct_points: 0.0
- latency_delta_ms: 923

## Mode Summary
| mode | runs | success_rate | avg_total_tokens | avg_latency_ms | total_cost_usd |
|---|---:|---:|---:|---:|---:|
| baseline | 4 | 25.0 | 5959 | 17556 | 0.002992 |
| elephant | 4 | 25.0 | 4202 | 18479 | 0.002314 |

## Per-Task Runs
| task_id | mode | success | total_tokens | latency_ms | cost_usd | retries | selected_model |
|---|---|---|---:|---:|---:|---:|---|
| dummy_summary_01 | baseline | True | 5749 | 22792 | 0.000542 | 0 | qwen/qwen3-coder-next |
| dummy_summary_01 | elephant | True | 3852 | 25234 | 0.000412 | 0 | qwen/qwen3-coder-next |
| dummy_feature_02 | baseline | False | 5893 | 26036 | 0.000573 | 0 | qwen/qwen3-coder-next |
| dummy_feature_02 | elephant | False | 4287 | 6145 | 0.001066 | 0 | qwen/qwen3-coder-next |
| dummy_feature_03 | baseline | False | 5775 | 15462 | 0.000488 | 0 | qwen/qwen3-coder-next |
| dummy_feature_03 | elephant | False | 4162 | 16073 | 0.000374 | 0 | qwen/qwen3-coder-next |
| dummy_invariant_04 | baseline | False | 6421 | 5935 | 0.001389 | 0 | qwen/qwen3-coder-next |
| dummy_invariant_04 | elephant | False | 4510 | 26467 | 0.000461 | 0 | qwen/qwen3-coder-next |
