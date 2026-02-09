# Elephant Coder v1 Spec

## 1. Objective
Build a new CLI-first coding system that uses:
- Grilly for acceleration
- OpenRouter worker agents for coding tasks
- A main orchestrator ("main AI") that coordinates agents
- Persistent project-local memory with token-first context reduction

Primary success target:
- Reduce token usage by at least 50% versus baseline mode.

## 2. Locked Decisions
- Build new implementation (not extending old server as the core runtime).
- Start with CLI.
- v1 language support: Python only.
- OpenRouter default development model: `gpt-4o-mini`.
- Token and cost limits: configurable.
- Output modes: human-readable and JSON.
- Persona format: Markdown files (`.md`).
- Plugins: external plugins allowed, permission-gated.
- Storage: project-local.
- Priority: token saving over all secondary optimizations.

## 3. Scope
### In scope (v1)
- Command router with commands:
  - `/plan`
  - `/code`
  - `/agents`
  - `/persona`
  - `/plugins`
  - `/git`
  - `/stats`
  - `/test`
- Global shared context + agent-private context + session context.
- Auto-indexing for Python files.
- Impact prediction across files/symbols.
- Context reduction pipeline before every model call.
- OpenRouter dispatch for one or more worker agents.
- Project-local persistence.

### Out of scope (v1)
- JS/TS indexing (target v1.1+).
- UI beyond CLI.
- Unrestricted plugin execution.

## 4. CLI Contract
### 4.1 Entry points
- Non-interactive:
  - `elephant <command> [flags]`
- Interactive shell:
  - Slash commands (`/plan`, `/code`, etc.)
- Output flag:
  - `--output text|json` (default: `text`)

### 4.2 Shared request fields
- `--task "<text>"` or stdin body
- `--cwd <path>` (default: current working directory)
- `--session <id>` (optional)
- `--persona <name>` (optional)
- `--max-input-tokens <int>` (optional override)
- `--max-output-tokens <int>` (optional override)
- `--max-cost-usd <float>` (optional override)

### 4.3 Shared JSON response envelope
```json
{
  "ok": true,
  "command": "/code",
  "run_id": "run_...",
  "session_id": "sess_...",
  "data": {},
  "metrics": {
    "input_tokens": 0,
    "output_tokens": 0,
    "total_tokens": 0,
    "estimated_cost_usd": 0.0,
    "latency_ms": 0
  },
  "warnings": [],
  "errors": []
}
```

## 5. Command Behavior
### 5.1 `/plan`
- Produces an implementation plan with impacted files and risk notes.
- Must use index + impact graph + memory retrieval before planning.
- JSON data fields:
  - `plan_steps[]`
  - `impacted_files[]`
  - `assumptions[]`
  - `risks[]`

### 5.2 `/code`
- Executes coding task with orchestrator + worker agent(s).
- Must enforce token budget through context reducer.
- Can run in dry-run (`--dry-run`) mode to return patch plan only.
- JSON data fields:
  - `changes[]`
  - `files_touched[]`
  - `agent_reports[]`
  - `verification_summary`

### 5.3 `/agents`
- Lists active/available agent profiles and routing policy.
- Supports spawn/terminate/status for worker agents.
- JSON data fields:
  - `agents[]`
  - `routing_policy`
  - `default_model`

### 5.4 `/persona`
- Lists, validates, and sets persona markdown files.
- Supports active persona switching per session.
- JSON data fields:
  - `active_persona`
  - `available_personas[]`
  - `validation`

### 5.5 `/plugins`
- Lists/install/enables/disables external plugins.
- Every plugin action must pass permission policy checks.
- JSON data fields:
  - `plugins[]`
  - `requested_permissions[]`
  - `granted_permissions[]`

### 5.6 `/git`
- Summarizes repo state and predicts impact of staged/unstaged diffs.
- Can generate commit message proposals.
- JSON data fields:
  - `repo_status`
  - `changed_files[]`
  - `impact_report`

### 5.7 `/stats`
- Reports token/cost/latency/quality metrics and memory store health.
- Includes baseline-vs-elephant comparison when available.
- JSON data fields:
  - `token_metrics`
  - `cost_metrics`
  - `latency_metrics`
  - `quality_metrics`
  - `memory_metrics`

### 5.8 `/test`
- Runs configured validations for changed files.
- Supports selective tests based on impact graph.
- JSON data fields:
  - `tests_selected[]`
  - `tests_run[]`
  - `results`

## 6. Context Model
- `global_context`:
  - Shared project memory available to orchestrator and agents.
- `agent_context`:
  - Private, task-local memory for each agent.
- `session_context`:
  - User/session scoped intent and recent decisions.

Rules:
- Agent-private context is not automatically broadcast to other agents.
- Orchestrator decides what private findings are promoted to global context.
- Every model call must receive reduced context, not raw full context.

## 7. Configuration
Single project-local config file:
- `.elephant-coder/config.md`

Config domains:
- model routing (default `gpt-4o-mini`)
- token/cost caps
- output defaults
- plugin permission policy
- indexing scope

## 8. Error Contract
Standard error codes:
- `E_CONFIG`
- `E_BUDGET`
- `E_MODEL`
- `E_INDEX`
- `E_IMPACT`
- `E_PLUGIN_PERMISSION`
- `E_STORAGE`
- `E_TEST`

Behavior:
- CLI exits non-zero on `ok=false`.
- JSON mode always returns machine-readable `errors[]`.

## 9. Acceptance Criteria (v1)
- All eight commands implemented in both text and JSON output modes.
- Python project can be indexed incrementally with persisted graph state.
- Impact report identifies direct + transitive affected files/symbols.
- Multi-agent coding flow works with orchestrator arbitration.
- Plugin permission gate blocks unapproved capabilities.
- Stats include per-run token and estimated cost accounting.
- Benchmark protocol demonstrates at least 50% token reduction.

## 10. Post-v1 Roadmap
### 10.1 Gate: OpenRouter Stability
Before local model routing work begins, OpenRouter path must be considered stable:
- `/code` success rate meets project threshold over benchmark suite.
- Budget enforcement is reliable (tokens/cost/latency are logged and bounded).
- File apply/bootstrap flow is deterministic across supported languages.

### 10.2 v2 Target: GGUF Local Specialists + MoE Routing
After the gate above passes:
- Add GGUF model loader for local inference.
- Run local models as specialist workers (e.g., planner, patcher, reviewer, test triage).
- Extend orchestrator routing policy to support MoE-style expert selection between:
  - remote OpenRouter workers,
  - local GGUF specialists.
- Keep token-first policy and fall back to OpenRouter when local confidence is low.
