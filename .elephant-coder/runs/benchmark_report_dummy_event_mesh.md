# Elephant Benchmark Report

- generated_at_utc: 2026-02-09T20:35:56Z
- benchmark_id: dummy_event_mesh_20260209T203040Z
- protocol_version: v1
- comparison_track: strategy
- tasks_total: 4
- runs_total: 8

## Aggregate
- token_reduction_pct: 21.0
- quality_delta_pct_points: 0.0
- latency_delta_ms: 10873

## Mode Summary
| mode | runs | success_rate | avg_total_tokens | avg_latency_ms | total_cost_usd |
|---|---:|---:|---:|---:|---:|
| baseline | 4 | 25.0 | 3662 | 15116 | 0.003525 |
| elephant | 4 | 25.0 | 2893 | 25989 | 0.001383 |

## Per-Task Runs
| task_id | mode | success | total_tokens | latency_ms | cost_usd | retries | selected_model |
|---|---|---|---:|---:|---:|---:|---|
| event_summary_01 | baseline | True | 3325 | 18504 | 0.000335 | 0 | qwen/qwen3-coder-next |
| event_summary_01 | elephant | True | 2374 | 19538 | 0.000267 | 0 | qwen/qwen3-coder-next |
| event_feature_02 | baseline | False | 3701 | 5959 | 0.001750 | 0 | qwen/qwen3-coder-next |
| event_feature_02 | elephant | False | 2794 | 27625 | 0.000361 | 0 | qwen/qwen3-coder-next |
| event_feature_03 | baseline | False | 3570 | 27784 | 0.000400 | 0 | qwen/qwen3-coder-next |
| event_feature_03 | elephant | False | 2828 | 19870 | 0.000299 | 0 | qwen/qwen3-coder-next |
| event_invariant_04 | baseline | False | 4054 | 8219 | 0.001041 | 0 | qwen/qwen3-coder-next |
| event_invariant_04 | elephant | False | 3578 | 36925 | 0.000456 | 0 | qwen/qwen3-coder-next |
