# Architectural Invariants

This document describes the extension contracts and architectural invariants that must be upheld by all implementations in the policy engine.

## Overview

The policy engine enforces a strict separation of concerns through abstract contracts. All concrete implementations must adhere to these contracts to ensure interoperability and predictable runtime behavior.

## Extension Contracts

### 1. Processor Contract (`src/policy_engine/contracts/processor.py`)

All channel-specific processors must inherit from `Processor` and implement:

- `name: str`: Human-readable identifier for the processor.
- `supports(item: WorkItem) -> bool`: Determines whether the processor can handle a given work item.
- `process(item: WorkItem) -> RunResult`: Executes processing logic and returns a structured result.

**Invariants:**
- `supports()` must be deterministic and side-effect-free.
- `process()` must not mutate the input `WorkItem`.
- `RunResult` must accurately reflect success/failure state and include sufficient details for debugging.

### 2. Repository Contract (`src/policy_engine/contracts/repository.py`)

All persistence layers must implement `WorkItemRepository` with:

- `save(item: WorkItem) -> None`: Persist a work item.
- `get(identifier: str) -> WorkItem | None`: Retrieve by ID.
- `list_by_channel(channel: str) -> list[WorkItem]`: Filter by target channel.
- `list_all() -> list[WorkItem]`: Retrieve all stored items.

**Invariants:**
- `save()` must ensure idempotent persistence (no duplicates for same ID).
- `get()` must return `None` if no item exists for the given ID.
- All list operations must return fresh copies to prevent external mutation.

### 3. Registry Contract (Implicit)

While no explicit `Registry` contract exists yet, the runtime (`build_default_runtime()`) enforces:

- Processors are registered by channel name.
- Dispatch logic selects processors via `supports()` checks.
- Repositories are used internally for auditability and recovery.

**Invariants:**
- Registry must ensure exactly one processor per channel.
- Processor registration must be immutable after runtime initialization.

## Work Item Contract (`src/policy_engine/contracts/work_item.py`)

All work items must implement:

- `identifier: str`: Unique, stable ID for traceability.
- `channel: str`: Target delivery channel (e.g., "email", "push").
- `payload: dict[str, str]`: Message content.

**Invariants:**
- `identifier` must be immutable after construction.
- `payload` must be shallow-copied on access to prevent external mutation.

## Runtime Behavior

These invariants ensure:
- Deterministic dispatch via `supports()` checks.
- Idempotent persistence via repository contracts.
- Traceability through stable identifiers and structured results.

Violations of these invariants may cause runtime errors or inconsistent state but must not alter the documented behavior of `run_dispatch_demo.py`.
