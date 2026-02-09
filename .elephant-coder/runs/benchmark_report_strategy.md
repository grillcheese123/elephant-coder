# Elephant Benchmark Report

- generated_at_utc: 2026-02-09T00:27:18Z
- benchmark_id: full_strategy_20260209a
- protocol_version: v1
- comparison_track: strategy
- tasks_total: 20
- runs_total: 40

## Aggregate
- token_reduction_pct: 72.19
- quality_delta_pct_points: 0.0
- latency_delta_ms: -3203

## Mode Summary
| mode | runs | success_rate | avg_total_tokens | avg_latency_ms | total_cost_usd |
|---|---:|---:|---:|---:|---:|
| baseline | 20 | 100.0 | 19854 | 15462 | 0.050157 |
| elephant | 20 | 100.0 | 5521 | 12259 | 0.016773 |

## Per-Task Runs
| task_id | mode | success | total_tokens | latency_ms | cost_usd | retries | selected_model |
|---|---|---|---:|---:|---:|---:|---|
| bugfix_01 | baseline | True | 20926 | 23942 | 0.002133 | 0 | qwen/qwen3-coder-next |
| bugfix_01 | elephant | True | 4207 | 2882 | 0.001053 | 0 | qwen/qwen3-coder-next |
| bugfix_02 | baseline | True | 18454 | 5339 | 0.001401 | 0 | qwen/qwen3-coder-next |
| bugfix_02 | elephant | True | 5248 | 13957 | 0.001775 | 0 | qwen/qwen3-coder-next |
| bugfix_03 | baseline | True | 20941 | 18912 | 0.002134 | 0 | qwen/qwen3-coder-next |
| bugfix_03 | elephant | True | 4623 | 5193 | 0.000450 | 0 | qwen/qwen3-coder-next |
| bugfix_04 | baseline | True | 19428 | 11669 | 0.001684 | 0 | qwen/qwen3-coder-next |
| bugfix_04 | elephant | True | 4982 | 8558 | 0.000562 | 0 | qwen/qwen3-coder-next |
| bugfix_05 | baseline | True | 18359 | 5291 | 0.002993 | 0 | qwen/qwen3-coder-next |
| bugfix_05 | elephant | True | 6413 | 19647 | 0.000982 | 0 | qwen/qwen3-coder-next |
| feature_01 | baseline | True | 20937 | 23230 | 0.002134 | 0 | qwen/qwen3-coder-next |
| feature_01 | elephant | True | 6131 | 13555 | 0.000914 | 0 | qwen/qwen3-coder-next |
| feature_02 | baseline | True | 18780 | 7136 | 0.001496 | 0 | qwen/qwen3-coder-next |
| feature_02 | elephant | True | 7007 | 18321 | 0.001169 | 0 | qwen/qwen3-coder-next |
| feature_03 | baseline | True | 20929 | 18890 | 0.002133 | 0 | qwen/qwen3-coder-next |
| feature_03 | elephant | True | 5970 | 12236 | 0.000855 | 0 | qwen/qwen3-coder-next |
| feature_04 | baseline | True | 20936 | 18867 | 0.002134 | 0 | qwen/qwen3-coder-next |
| feature_04 | elephant | True | 4400 | 5496 | 0.000473 | 0 | qwen/qwen3-coder-next |
| feature_05 | baseline | True | 18227 | 3287 | 0.001332 | 0 | qwen/qwen3-coder-next |
| feature_05 | elephant | True | 5286 | 9204 | 0.000653 | 0 | qwen/qwen3-coder-next |
| refactor_01 | baseline | True | 20943 | 20564 | 0.008008 | 0 | qwen/qwen3-coder-next |
| refactor_01 | elephant | True | 5155 | 9678 | 0.000696 | 0 | qwen/qwen3-coder-next |
| refactor_02 | baseline | True | 20940 | 18491 | 0.002134 | 0 | qwen/qwen3-coder-next |
| refactor_02 | elephant | True | 4370 | 4839 | 0.000451 | 0 | qwen/qwen3-coder-next |
| refactor_03 | baseline | True | 20622 | 21912 | 0.002042 | 0 | qwen/qwen3-coder-next |
| refactor_03 | elephant | True | 5506 | 12434 | 0.000788 | 0 | qwen/qwen3-coder-next |
| refactor_04 | baseline | True | 20938 | 34997 | 0.005040 | 0 | qwen/qwen3-coder-next |
| refactor_04 | elephant | True | 4437 | 4474 | 0.000408 | 0 | qwen/qwen3-coder-next |
| refactor_05 | baseline | True | 20936 | 24433 | 0.002134 | 0 | qwen/qwen3-coder-next |
| refactor_05 | elephant | True | 5287 | 9934 | 0.000719 | 0 | qwen/qwen3-coder-next |
| test_01 | baseline | True | 18521 | 6968 | 0.001419 | 0 | qwen/qwen3-coder-next |
| test_01 | elephant | True | 5407 | 12717 | 0.000749 | 0 | qwen/qwen3-coder-next |
| test_02 | baseline | True | 19926 | 14932 | 0.001834 | 0 | qwen/qwen3-coder-next |
| test_02 | elephant | True | 6609 | 20642 | 0.001043 | 0 | qwen/qwen3-coder-next |
| test_03 | baseline | True | 18583 | 8696 | 0.003173 | 0 | qwen/qwen3-coder-next |
| test_03 | elephant | True | 6968 | 22393 | 0.001166 | 0 | qwen/qwen3-coder-next |
| test_04 | baseline | True | 18614 | 8114 | 0.003194 | 0 | qwen/qwen3-coder-next |
| test_04 | elephant | True | 5431 | 14193 | 0.000701 | 0 | qwen/qwen3-coder-next |
| test_05 | baseline | True | 19152 | 13587 | 0.001604 | 0 | qwen/qwen3-coder-next |
| test_05 | elephant | True | 6996 | 24841 | 0.001168 | 0 | qwen/qwen3-coder-next |
