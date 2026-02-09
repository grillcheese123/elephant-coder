# Benchmark Comparison: Strategy vs Prompt-Parity

- generated_at_utc: 2026-02-09T00:41:36Z
- strategy_benchmark_id: full_strategy_20260209a
- prompt_parity_benchmark_id: full_prompt_parity_20260209a
- tasks_total: 20
- runs_per_track: 40

## Aggregate Comparison
| metric | strategy | prompt-parity |
|---|---:|---:|
| token_reduction_pct | 72.19 | 0.23 |
| baseline_avg_tokens | 19854 | 20284 |
| elephant_avg_tokens | 5521 | 20238 |
| baseline_total_cost_usd | 0.050157 | 0.068754 |
| elephant_total_cost_usd | 0.016773 | 0.051772 |
| cost_saved_usd | 0.033384 | 0.016982 |
| cost_reduction_pct | 66.56 | 24.7 |
| quality_delta_pct_points | 0 | 0 |
| latency_delta_ms | -3203 | -1337 |
| baseline_success_rate | 100 | 100 |
| elephant_success_rate | 100 | 100 |

## Interpretation
- strategy track captures real-world product behavior (memory/context optimization included).
- prompt-parity track controls for prompt-construction differences and behaves as an ablation baseline.
- observed token-saving uplift attributable to strategy effects: 71.96 percentage points.
