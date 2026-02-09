# Elephant Coder Benchmark Protocol (v1)

## 1. Goal
Measure whether Elephant Coder achieves the primary target:
- at least 50% token reduction versus baseline.

Secondary goal:
- maintain acceptable coding quality while reducing tokens.

## 2. Compared Modes
### 2.1 Baseline mode
- No persistent memory retrieval.
- No impact-aware context reduction.
- Standard direct prompting with relevant files only.

### 2.2 Elephant mode
- Uses indexing + impact prediction.
- Uses global/agent/session memory retrieval.
- Uses context reduction and strict budget gating.

### 2.3 Comparison tracks
- `strategy` (default):
  - Compares baseline and elephant with their native context strategies.
  - Measures product-realistic savings.
- `prompt-parity`:
  - Forces identical prompt-construction behavior for both modes.
  - Disables elephant-only session-context compression effects for the run.
  - Measures model/path variance under same prompt construction.

## 3. Test Corpus
v1 corpus:
- This repository (`grilly`) only.
- Python tasks only.

## 4. Task Suite (v1)
Minimum 20 tasks total, split evenly:
1. Bug fix tasks (5)
2. Feature extension tasks (5)
3. Refactor tasks (5)
4. Test-writing or test-fix tasks (5)

Task requirements:
- Each task has a written prompt.
- Each task has expected files likely affected.
- Each task has objective acceptance checks.

## 5. Model and Runtime Controls
- Default dev model: `gpt-4o-mini`.
- Same model and caps for both modes unless a run explicitly tests routing.
- Fixed randomness settings where supported.
- No manual intervention during run execution.

## 6. Run Procedure
For each task:
1. Reset workspace to clean task start state.
2. Execute Baseline mode once.
3. Execute Elephant mode once.
4. Run acceptance checks for both outputs.
5. Record metrics.

Recommended reliability pass:
- Repeat each task 3 times and report mean and variance.

Recommended reporting:
- Run both comparison tracks:
  - `strategy` for real-world outcome.
  - `prompt-parity` as control/ablation.

## 7. Metrics
### 7.1 Primary KPI
- `token_reduction_pct`:
  - `(baseline_total_tokens - elephant_total_tokens) / baseline_total_tokens * 100`

Pass condition:
- Overall suite average `token_reduction_pct >= 50.0`.

### 7.2 Secondary metrics
- Success rate:
  - fraction of tasks passing acceptance checks.
- Quality delta:
  - Elephant success rate should not drop by more than 5 percentage points from baseline.
- Latency:
  - median runtime per task.
- Estimated cost:
  - per task and suite total.
- Retry count:
  - total model retries and failure types.

## 8. Acceptance Checks
Per task checks can include:
- target tests passing
- lint/type checks for touched files
- required file edits present
- no unexpected file regressions

Each task must define:
- mandatory checks
- optional checks

## 9. Logging Schema
Each run must log:
- `run_id`
- `task_id`
- `mode` (`baseline` or `elephant`)
- `model`
- `input_tokens`
- `output_tokens`
- `total_tokens`
- `estimated_cost_usd`
- `latency_ms`
- `success` (true/false)
- `checks_passed[]`
- `checks_failed[]`
- `files_touched[]`
- `retries`

## 10. Reporting
Produce two artifacts:
1. Machine-readable:
  - `.elephant-coder/runs/benchmark_results.json`
2. Human summary:
  - `.elephant-coder/runs/benchmark_report.md`

Required summary sections:
- aggregate token reduction
- per-task comparison table
- quality delta
- latency delta
- failure analysis

## 11. Failure Policy
If token target is met but quality regression is too high:
- fail benchmark and open quality remediation.

If quality is strong but token target is below 50%:
- fail benchmark and open context-compression remediation.

Release gate:
- both token and quality criteria must pass.

## 12. Versioning
- Protocol version: `v1`.
- Any metric definition change requires version increment and explicit changelog entry.
