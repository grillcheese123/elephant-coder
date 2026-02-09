# Capsule Transport Ablation Report

- generated_at_utc: 2026-02-09T20:23:44Z
- task_mode: same fixtures/tasks, same budgets; only capsule transport toggled
- capsule_mode: capsule_only

| fixture | text_token_reduction | capsule_token_reduction | delta_token_reduction | text_elephant_success | capsule_elephant_success | text_elephant_avg_tokens | capsule_elephant_avg_tokens |
|---|---:|---:|---:|---:|---:|---:|---:|
| dummy_oop | 36.18 | 33.89 | -2.29 | 100.00 | 100.00 | 3685 | 3796 |
| dummy_event_mesh | 30.87 | 28.91 | -1.96 | 100.00 | 100.00 | 2318 | 2402 |
| dummy_policy_engine | 29.09 | 28.84 | -0.25 | 100.00 | 100.00 | 2416 | 2408 |
| dummy_layered_inheritance | 22.77 | 28.88 | 6.11 | 100.00 | 100.00 | 3293 | 3175 |
| dummy_cross_module | 13.96 | 15.68 | 1.72 | 0.00 | 100.00 | 3025 | 2980 |

## Average Delta
- delta_token_reduction_pct_mean: 0.67
- delta_elephant_success_rate_mean: 20.00
- delta_elephant_avg_total_tokens_mean: 4.80
