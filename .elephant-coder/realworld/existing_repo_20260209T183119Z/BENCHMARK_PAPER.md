# Elephant Coder Benchmark Paper

## Token Efficiency Through Structured Context: VSA, Hippocampal Memory, Capsules, and Multimodal Context Packing

### Abstract
This paper explains how Elephant Coder achieved strong token and cost reductions on its benchmark suite, and how those gains connect to four architectural ideas: Vector Symbolic Architecture (VSA), hippocampal-style memory, capsule representations, and constrained multimodal context packing.

On the `strategy` track (real product behavior), Elephant reduced average tokens by **72.19%** relative to baseline while preserving quality (`100%` success in both modes). On the `prompt-parity` control track (prompt-construction parity forced), token reduction dropped to **0.23%**. This ablation strongly indicates that savings are not from random model variance, but from context strategy and memory design.

### Path Convention
All file paths referenced in this paper are relative to the Grilly framework root path (`grilly/` repository root), unless explicitly marked otherwise.

## 1. Benchmark Setup

### 1.1 Protocol
Benchmark protocol is defined in:
- `private/models/elephant-coder/BENCHMARK_PROTOCOL.md`

Suite characteristics:
- 20 tasks total
- Categories: bugfix (5), feature (5), refactor (5), test (5)
- Both `baseline` and `elephant` modes executed per task
- Inference-only runs (`--no-apply`) for clean token/cost accounting

### 1.2 Comparison Tracks
Two tracks were executed:
- `strategy`: each mode uses its native context strategy
- `prompt-parity`: parity flag forces the same prompt-construction behavior across modes

Artifacts:
- Strategy report: `private/models/elephant-coder/.elephant-coder/runs/benchmark_report_strategy.md`
- Prompt-parity report: `private/models/elephant-coder/.elephant-coder/runs/benchmark_report_prompt_parity.md`
- Side-by-side report: `private/models/elephant-coder/.elephant-coder/runs/benchmark_compare_strategy_vs_prompt_parity.md`

Benchmark IDs:
- `full_strategy_20260209a`
- `full_prompt_parity_20260209a`

## 2. Results Summary

### 2.1 Aggregate Outcomes
| Metric | Strategy | Prompt-Parity |
|---|---:|---:|
| token_reduction_pct | 72.19 | 0.23 |
| baseline_avg_tokens | 19,854 | 20,284 |
| elephant_avg_tokens | 5,521 | 20,238 |
| baseline_total_cost_usd | 0.050157 | 0.068754 |
| elephant_total_cost_usd | 0.016773 | 0.051772 |
| cost_reduction_pct | 66.56 | 24.70 |
| quality_delta_pct_points | 0.0 | 0.0 |
| baseline_success_rate | 100.0 | 100.0 |
| elephant_success_rate | 100.0 | 100.0 |

### 2.2 Main Empirical Claim
The drop from 72.19% (strategy) to 0.23% (prompt-parity) shows that Elephant's gains are primarily due to context/memory strategy, not model luck.

## 3. Context Architecture and Why It Works

Elephant's `/code` pipeline assembles a constrained multimodal context pack before each model call:
- impacted files (graph + world-model assisted)
- VSA structure and file ranking
- AST/graph features
- git diff
- code chunks
- recent runtime traces

This is implemented in `private/models/elephant-coder/scripts/elephant_cli.py` in:
- `_build_context_pack`
- `_vsa_rank_candidate_files`
- `_build_vsa_structure`
- `_collect_code_chunks`
- `_collect_ast_graph_features`
- `_collect_runtime_traces`

### 3.1 Why Baseline vs Elephant Diverge
In `strategy` mode, Elephant applies stricter context compression and session-aware context handling, while baseline uses larger prompt profiles. This changes prompt size distribution materially, which is exactly what the benchmark measured.

In `prompt-parity`, these strategic differences are deliberately neutralized, and the measured advantage largely disappears.

## 4. VSA Link: Structure-Preserving Compression and Ranking

VSA is used as a lightweight structural prior over context:
- candidate files are ranked by task similarity using bipolar vectors (`BinaryOps.hash_to_bipolar`, `similarity`)
- multiple modalities are converted into vectors and bundled
- bundle/task similarities and fingerprints are logged in manifest fields

Relevant implementation:
- `experimental/vsa/ops.py`
- `private/models/elephant-coder/scripts/elephant_cli.py` (`_vsa_rank_candidate_files`, `_build_vsa_structure`)

Interpretation:
- VSA provides fast, deterministic heuristics for "what context is most likely useful" before expensive LLM generation.
- This helps keep prompt payloads small without dropping all structural cues.

## 5. Hippocampal Memory Link: Recall, Completion, and Session Continuity

### 5.1 In Elephant Today
Elephant maintains project-local session traces and retrieves compact recent context for coding turns. It also computes impact using static graph traversal plus a cognitive world-model consequence predictor.

Key paths:
- session context loading: `private/models/elephant-coder/scripts/elephant_cli.py` (`_load_session_context`)
- impact + world prediction: `private/models/elephant-coder/elephant_coder/index_engine.py` (`impact_for_files`, `_build_cognitive_world`)

### 5.2 Hippocampal Analogy
This maps to hippocampal roles:
- recall from recent episodic traces (session memory)
- completion of likely consequences from partial change signals (world-model predictions)

Framework-level hippocampal building blocks exist in:
- `nn/hippocampal.py` (`HippocampalTransformerLayer`)

These include DG sparse expansion, CA3-like retrieval, and gated memory injection.

## 6. Capsule Link: Compact Semantic State

Capsule mechanisms in the framework compress dense embeddings into low-dimensional semantic state with optional DG expansion.

Relevant modules:
- `nn/capsule_embedding.py`
- `experimental/cognitive/world.py` (capsule-aware fact storage and coherence)

Important current detail:
- Elephant's index world model is currently instantiated with `capsule_dim=0` in `index_engine.py`, so capsule similarity is not active in the current benchmark path.

Implication:
- The benchmark gains reported here are mostly from VSA + impact graph + session/context strategy.
- Capsule-enabled world reasoning is available in framework code and is a clear extension path.

## 7. Unified Mechanistic View

The four pieces operate as a stack:
1. Graph/index impact narrows scope to likely affected files.
2. VSA ranks and fingerprints multimodal evidence quickly.
3. Hippocampal-style memory contributes temporal continuity and consequence prediction.
4. Capsule representations provide a compact semantic substrate for future richer recall/coherence checks.

The current benchmark validates that steps 1 to 3 already produce large practical token savings in real workflow mode.

## 8. Threats to Validity

- Single repository corpus (`grilly`)
- Python-centered indexing in current benchmark flow
- Model/provider dynamics can shift over time
- Inference-only benchmark mode (`--no-apply`) does not measure end-to-end file-application quality regressions

Mitigations used:
- dual-track evaluation (`strategy` + `prompt-parity`)
- identical task suite and budget caps across compared runs
- per-run machine-readable artifacts persisted in project-local storage

## 9. Reproducibility

Environment:
- Python 3.12
- `uv` runner

Commands:
```bash
uv run --python 3.12 python private/models/elephant-coder/scripts/benchmark_runner.py --cwd private/models/elephant-coder --comparison-track strategy --benchmark-id full_strategy_20260209a
uv run --python 3.12 python private/models/elephant-coder/scripts/benchmark_runner.py --cwd private/models/elephant-coder --comparison-track prompt-parity --benchmark-id full_prompt_parity_20260209a
```

Comparison artifact:
- `private/models/elephant-coder/.elephant-coder/runs/benchmark_compare_strategy_vs_prompt_parity.md`

## 10. Conclusion

Elephant's benchmark advantage is real under product conditions and largely attributable to structured context strategy, not baseline model variance. The ablation result (72.19% vs 0.23%) is strong evidence that memory-aware context engineering is the dominant factor.

VSA gives fast structure-aware ranking and compression, hippocampal-style mechanisms provide recall and consequence continuity, and capsules provide a pathway for richer semantic memory state. Together, they form a coherent architecture for high-quality, lower-token coding assistance.
