# Architectural Invariants

This document describes the extension contracts and architectural invariants that must be preserved when extending the Policy Engine.

## Overview

The Policy Engine enforces strict architectural boundaries through abstract contracts. All extensions must adhere to these contracts to ensure correct dispatching, processing, and persistence behavior.

## Extension Contracts

### 1. Processor Contract (`src/policy_engine/contracts/processor.py`)

All channel-specific processors must implement the `Processor` abstract base class:

- **`name: str`** (property): Human-readable identifier for the processor.
- **`supports(item: WorkItem) -> bool`**: Determines whether this processor can handle a given work item.
- **`process(item: WorkItem) -> RunResult`**: Executes processing logic and returns a structured result.

#### Inheritance Rules

- Processors must be registered in the runtime registry to be dispatchable.
- `supports()` must be deterministic and consistent for a given item.
- `process()` must not mutate the input `WorkItem`.
- All exceptions during processing must be caught and reflected in `RunResult.success` and `details`.

### 2. Repository Contract (`src/policy_engine/contracts/repository.py`)

All persistence layers must implement the `WorkItemRepository` abstract base class:

- **`save(item: WorkItem) -> None`**: Persist a work item.
- **`get(identifier: str) -> WorkItem | None`**: Retrieve a work item by ID.
- **`list_by_channel(channel: str) -> list[WorkItem]`**: List items targeting a specific channel.
- **`list_all() -> list[WorkItem]`**: List all stored items.

#### Invariants

- `save()` must be idempotent for the same item.
- `get()` must return `None` if the item does not exist.
- `list_by_channel()` and `list_all()` must return fresh copies or immutable views to prevent external mutation.

### 3. Registry Contract (Implicit)

The runtime maintains an internal registry mapping channel names to processor instances. While not explicitly defined as a contract class, the registry enforces:

- Each channel maps to exactly one processor.
- Processors must be registered before dispatching items for that channel.
- Attempting to dispatch to an unregistered channel raises `LookupError`.

## Work Item Contract (`src/policy_engine/contracts/work_item.py`)

All work items must implement:

- **`identifier: str`**: Stable, unique ID for traceability.
- **`channel: str`**: Target delivery channel (e.g., `email`, `push`).
- **`payload: dict[str, str]`**: Message payload.

## Runtime Behavior Preservation

All invariants above must be maintained to ensure:

- `runtime.dispatch(ticket)` behaves deterministically.
- Dispatching to unsupported channels raises `LookupError`.
- Processing results are correctly captured in `RunResult` objects.
- Persistence operations do not corrupt or lose work items.

## Summary

Extensions must:

1. Implement `Processor`, `WorkItemRepository`, and `WorkItem` contracts exactly.
2. Register processors in the runtime registry before dispatch.
3. Preserve immutability and idempotency in processing and persistence.
4. Handle errors gracefully via `RunResult` instead of propagating exceptions.

Violating these invariants may cause runtime failures or inconsistent state.