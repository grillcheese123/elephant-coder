# Synthetic Fixture Benchmark Scenarios

All paths in this document are relative to the Grilly repository root.

## Purpose
Provide synthetic but realistic inheritance-heavy projects for benchmarking:
- source summarization quality
- structure-aware coding behavior
- correct use of abstract contracts and class extension patterns

## Fixtures
1. `private/models/elephant-coder/.benchmarks/fixtures/dummy_oop_project`
2. `private/models/elephant-coder/.benchmarks/fixtures/dummy_event_mesh_project`
3. `private/models/elephant-coder/.benchmarks/fixtures/dummy_policy_engine_project`
4. `private/models/elephant-coder/.benchmarks/fixtures/dummy_layered_inheritance_project`
5. `private/models/elephant-coder/.benchmarks/fixtures/dummy_cross_module_project`

Each fixture includes:
- abstract contracts (`WorkItem`, `Processor`, `WorkItemRepository`)
- base/concrete inheritance chain (`BaseProcessor` -> `Email/Sms/Webhook`)
- runtime wiring (`registry`, `bootstrap`, `dispatcher`)
- unit tests validating behavior

## Task Suites
- `private/models/elephant-coder/.benchmarks/tasks_dummy_oop_v1.json`
- `private/models/elephant-coder/.benchmarks/tasks_dummy_event_mesh_v1.json`
- `private/models/elephant-coder/.benchmarks/tasks_dummy_policy_engine_v1.json`
- `private/models/elephant-coder/.benchmarks/tasks_dummy_layered_inheritance_v1.json`
- `private/models/elephant-coder/.benchmarks/tasks_dummy_cross_module_v1.json`

Tasks:
1. Summarize architecture into `docs/summary/project_architecture.md`.
2. Add push support by inferring existing extension rules (no explicit base-class name in prompt).
3. Add demo script to dispatch email + push flows and print a summary.

## Runners
- Single scenario runner:
  - `private/models/elephant-coder/scripts/dummy_oop_benchmark_runner.py`
- Multi-scenario runner:
  - `private/models/elephant-coder/scripts/multi_fixture_benchmark_runner.py`

Single-scenario runner will:
1. Copy the fixture into an isolated target under `.elephant-coder/realworld/`.
2. Write scenario config (`cognition.world_model.*` dimensions).
3. Run benchmark tasks in both modes with checks enabled.
4. Persist dedicated outputs using the chosen `--results-prefix`.

Multi-scenario runner executes all five fixtures and writes:
- `.elephant-coder/runs/multi_fixture_summary.md`

## Example Commands
```bash
uv run --python 3.12 python private/models/elephant-coder/scripts/dummy_oop_benchmark_runner.py --framework-root private/models/elephant-coder --world-dim 768 --capsule-dim 48
uv run --python 3.12 python private/models/elephant-coder/scripts/multi_fixture_benchmark_runner.py --framework-root private/models/elephant-coder
```
