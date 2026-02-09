# Elephant Benchmark Report

- generated_at_utc: 2026-02-09T00:41:05Z
- benchmark_id: full_prompt_parity_20260209a
- protocol_version: v1
- comparison_track: prompt-parity
- tasks_total: 20
- runs_total: 40

## Aggregate
- token_reduction_pct: 0.23
- quality_delta_pct_points: 0.0
- latency_delta_ms: -1337

## Mode Summary
| mode | runs | success_rate | avg_total_tokens | avg_latency_ms | total_cost_usd |
|---|---:|---:|---:|---:|---:|
| baseline | 20 | 100.0 | 20284 | 21072 | 0.068754 |
| elephant | 20 | 100.0 | 20238 | 19735 | 0.051772 |

## Per-Task Runs
| task_id | mode | success | total_tokens | latency_ms | cost_usd | retries | selected_model |
|---|---|---|---:|---:|---:|---:|---|
| bugfix_01 | baseline | True | 20926 | 23716 | 0.002133 | 0 | qwen/qwen3-coder-next |
| bugfix_01 | elephant | True | 20926 | 18545 | 0.002133 | 0 | qwen/qwen3-coder-next |
| bugfix_02 | baseline | True | 20916 | 21918 | 0.002133 | 0 | qwen/qwen3-coder-next |
| bugfix_02 | elephant | True | 18528 | 7793 | 0.003145 | 0 | qwen/qwen3-coder-next |
| bugfix_03 | baseline | True | 20941 | 20636 | 0.008007 | 0 | qwen/qwen3-coder-next |
| bugfix_03 | elephant | True | 20941 | 20200 | 0.002134 | 0 | qwen/qwen3-coder-next |
| bugfix_04 | baseline | True | 19380 | 13782 | 0.003801 | 0 | qwen/qwen3-coder-next |
| bugfix_04 | elephant | True | 19835 | 14225 | 0.001805 | 0 | qwen/qwen3-coder-next |
| bugfix_05 | baseline | True | 18222 | 3351 | 0.001326 | 0 | qwen/qwen3-coder-next |
| bugfix_05 | elephant | True | 18915 | 8309 | 0.001532 | 0 | qwen/qwen3-coder-next |
| feature_01 | baseline | True | 20820 | 42176 | 0.004947 | 0 | qwen/qwen3-coder-next |
| feature_01 | elephant | True | 20937 | 21999 | 0.002134 | 0 | qwen/qwen3-coder-next |
| feature_02 | baseline | True | 20926 | 19512 | 0.002133 | 0 | qwen/qwen3-coder-next |
| feature_02 | elephant | True | 20926 | 20301 | 0.002133 | 0 | qwen/qwen3-coder-next |
| feature_03 | baseline | True | 20929 | 24355 | 0.002133 | 0 | qwen/qwen3-coder-next |
| feature_03 | elephant | True | 20929 | 22189 | 0.002133 | 0 | qwen/qwen3-coder-next |
| feature_04 | baseline | True | 20936 | 21667 | 0.002134 | 0 | qwen/qwen3-coder-next |
| feature_04 | elephant | True | 20936 | 38815 | 0.005039 | 0 | qwen/qwen3-coder-next |
| feature_05 | baseline | True | 20924 | 24673 | 0.002133 | 0 | qwen/qwen3-coder-next |
| feature_05 | elephant | True | 20924 | 26247 | 0.002133 | 0 | qwen/qwen3-coder-next |
| refactor_01 | baseline | True | 20943 | 19998 | 0.008008 | 0 | qwen/qwen3-coder-next |
| refactor_01 | elephant | True | 20943 | 30530 | 0.005041 | 0 | qwen/qwen3-coder-next |
| refactor_02 | baseline | True | 20940 | 62131 | 0.012444 | 0 | qwen/qwen3-coder-next |
| refactor_02 | elephant | True | 20940 | 21060 | 0.002134 | 0 | qwen/qwen3-coder-next |
| refactor_03 | baseline | True | 20932 | 31877 | 0.005039 | 0 | qwen/qwen3-coder-next |
| refactor_03 | elephant | True | 20703 | 37895 | 0.004858 | 0 | qwen/qwen3-coder-next |
| refactor_04 | baseline | True | 20938 | 24028 | 0.002134 | 0 | qwen/qwen3-coder-next |
| refactor_04 | elephant | True | 20938 | 29103 | 0.005040 | 0 | qwen/qwen3-coder-next |
| refactor_05 | baseline | True | 20936 | 18742 | 0.002134 | 0 | qwen/qwen3-coder-next |
| refactor_05 | elephant | True | 20936 | 22739 | 0.002134 | 0 | qwen/qwen3-coder-next |
| test_01 | baseline | True | 19283 | 10906 | 0.001646 | 0 | qwen/qwen3-coder-next |
| test_01 | elephant | True | 19377 | 10983 | 0.001674 | 0 | qwen/qwen3-coder-next |
| test_02 | baseline | True | 19762 | 13458 | 0.001785 | 0 | qwen/qwen3-coder-next |
| test_02 | elephant | True | 19507 | 11770 | 0.001709 | 0 | qwen/qwen3-coder-next |
| test_03 | baseline | True | 18792 | 7084 | 0.001496 | 0 | qwen/qwen3-coder-next |
| test_03 | elephant | True | 19233 | 12578 | 0.001627 | 0 | qwen/qwen3-coder-next |
| test_04 | baseline | True | 19162 | 9443 | 0.001605 | 0 | qwen/qwen3-coder-next |
| test_04 | elephant | True | 18629 | 6165 | 0.001447 | 0 | qwen/qwen3-coder-next |
| test_05 | baseline | True | 19082 | 8003 | 0.001583 | 0 | qwen/qwen3-coder-next |
| test_05 | elephant | True | 19767 | 13262 | 0.001787 | 0 | qwen/qwen3-coder-next |
