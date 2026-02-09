# Elephant Coder v1 Architecture Contract

## 1. Purpose
Define the implementation contract for a new CLI-first system that:
- orchestrates OpenRouter coding agents,
- uses Grilly for acceleration,
- manages global and agent-private context,
- and minimizes token usage.

This document is the required architecture baseline before implementation code.

## 2. Top-Level Components
1. CLI Runtime
2. Orchestrator Core (main AI)
3. Agent Runtime (OpenRouter workers)
4. Context and Memory System
5. Indexing and Impact Graph
6. Context Reduction Engine
7. Persona System (markdown)
8. Plugin Runtime (permission-gated)
9. Observability and Stats

## 3. Component Responsibilities
### 3.1 CLI Runtime
- Parse command and flags.
- Validate request schema.
- Route command to orchestrator APIs.
- Render text/json output.
- Return deterministic exit codes.

### 3.2 Orchestrator Core
- Owns control flow for all commands.
- Decides agent count/model/routing.
- Performs arbitration of agent outputs.
- Promotes selected agent findings to global memory.
- Enforces token/cost budgets.

### 3.3 Agent Runtime
- Executes assigned task units with OpenRouter.
- Maintains private agent context.
- Reports structured output to orchestrator.
- Never mutates global context directly.

### 3.4 Context and Memory
- Three logical stores:
  - global shared project memory
  - agent-private memory
  - session memory
- Persistent storage is project-local.
- Provides retrieval APIs with recency/relevance scoring.

### 3.5 Index + Impact
- Incremental Python indexing:
  - symbol extraction
  - import graph
  - call edges
  - file hash + mtime tracking
- Impact engine computes:
  - direct impact
  - transitive impact
  - confidence score

### 3.6 Context Reduction Engine
- Produces compact context packs from retrieved candidates.
- Deduplicates and ranks by:
  - direct impact relevance
  - dependency proximity
  - recency/frequency
  - persona/task constraints
- Enforces hard token budgets before dispatch.

### 3.7 Persona System
- Personas stored as markdown files.
- Each persona declares:
  - style constraints
  - risk tolerance
  - coding posture
  - tool usage policy
- Orchestrator loads persona into planning and routing behavior.

### 3.8 Plugin Runtime
- Supports external plugins.
- Plugins request explicit permissions.
- Permissions are checked before execution.
- Plugin actions are logged for auditing.

### 3.9 Observability
- Per-run metrics:
  - tokens in/out/total
  - estimated cost
  - latency
  - retries
  - failures
- Store per-command and per-agent traces.

## 4. Data Flow (Canonical `/code` Request)
1. CLI receives `/code`.
2. Orchestrator resolves config/persona/budgets.
3. Index/impact service computes affected graph region.
4. Context reducer builds minimal context pack.
5. Orchestrator assigns tasks to one or more agents.
6. Agents execute with private context.
7. Orchestrator merges and validates outputs.
8. Global/session memory updated.
9. Stats recorded and response returned.

## 5. Storage Contract (Project Local)
Root:
- `.elephant-coder/`

Planned layout:
- `.elephant-coder/state.db`
- `.elephant-coder/runs/`
- `.elephant-coder/personas/`
- `.elephant-coder/plugins/`
- `.elephant-coder/cache/`
- `.elephant-coder/checkpoints/`

## 6. Logical Data Model
Required entities:
- `runs`
- `sessions`
- `global_memories`
- `agent_memories`
- `indexed_files`
- `symbols`
- `edges`
- `impacts`
- `personas`
- `plugins`
- `plugin_permissions`
- `metrics`

Core relationship constraints:
- A run belongs to one session.
- Agent memories belong to one run and one agent.
- Global memories are run-derived but project-shared.
- Impact rows are derived from graph edges + changed symbols.

## 7. Permission Model (Plugins)
Base permissions:
- `read_fs`
- `write_fs`
- `exec_shell`
- `network_outbound`
- `vcs_modify`
- `secrets_access`

Rules:
- Deny by default.
- Allow list is configured per project.
- Permission decisions are explicit and auditable.
- Command execution fails with `E_PLUGIN_PERMISSION` if denied.

## 8. Acceleration Contract (Grilly)
Grilly acceleration targets:
- similarity scoring for retrieval ranking
- batched vector ops for context prioritization
- optional graph scoring kernels

Fallback:
- CPU implementations must exist for functional parity.

## 9. Model Routing Contract
Default development route:
- `gpt-4o-mini`

Configurable policies:
- task type -> model tier mapping
- retry and fallback chain
- max tokens and max cost per run/command

Hard rule:
- budget checks happen before every model call.

## 10. Reliability and Recovery
- Writes are atomic at command boundary.
- Crash-safe run logging.
- Rebuild index command must recover from partial state.
- Stale memory detection on file changes/deletes.

## 11. Versioning
- Architecture version: `v1`.
- Any schema-breaking change must bump architecture version and include migration notes.

## 12. v1 Boundaries
- Python indexing only.
- CLI only (no web UI).
- Permission-gated external plugins.
- Token optimization takes precedence when tradeoffs occur.

## 13. Post-v1 Extension (Planned)
### 13.1 Readiness Gate
Enable local specialist routing only after OpenRouter path is stable in production-like runs:
- low failure rate under benchmark protocol,
- predictable budget enforcement,
- reliable apply-to-disk workflow.

### 13.2 GGUF Specialist Runtime
Add a local inference subsystem that can:
- load one or more GGUF models,
- expose specialist roles (planner/patcher/reviewer/test specialist),
- run offline/low-latency inference for local workflows.

### 13.3 MoE Routing Integration
Extend model routing so orchestrator can route each unit of work to:
- OpenRouter remote model, or
- local GGUF specialist.

Routing signals:
- task type,
- confidence/quality priors,
- latency and cost budget,
- privacy/offline requirements.

Fallback rule:
- if local specialist confidence is below threshold, escalate to OpenRouter.
