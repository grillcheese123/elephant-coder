# Architectural Invariants

This document describes extension contracts and architectural invariants that must be upheld for correct extension of the policy engine.

## Overview

The policy engine enforces a layered architecture with clearly defined contracts for extensibility. Extensions must conform to these contracts to ensure runtime correctness and interoperability.

## Extension Contracts

### 1. Processor Contract

All channel-specific processors must implement the `Processor` abstract base class (`src/policy_engine/contracts/processor.py`).

#### Required Invariants

- **`name` property**: Must return a stable, human-readable identifier for the processor.
- **`supports(item: WorkItem) -> bool`**: Must deterministically decide whether the processor can handle a given work item based on its channel and payload.
- **`process(item: WorkItem) -> RunResult`**: Must process the item and return a `RunResult` with accurate success/failure status and details.

#### Inheritance Rules

- Processors must be registered in the runtime registry to be dispatchable.
- Processors must not mutate the input `WorkItem`—they may only read its properties.
- Processors must be idempotent where possible (same input → same output).

### 2. Repository Contract

All persistence layers must implement the `WorkItemRepository` abstract base class (`src/policy_engine/contracts/repository.py`).

#### Required Invariants

- **`save(item: WorkItem)`**: Must persist the item without altering its identity or channel.
- **`get(identifier: str) -> WorkItem | None`**: Must return the exact item previously saved, or `None` if not found.
- **`list_by_channel(channel: str) -> list[WorkItem]`**: Must return all items matching the channel, without side effects.
- **`list_all() -> list[WorkItem]`**: Must return all stored items.

#### Implementation Rules

- Repositories must preserve immutability semantics of `WorkItem` instances.
- Repositories must not filter or transform items—only persist and retrieve.

### 3. Registry Contract

The runtime maintains a registry of processors keyed by channel name. While not a formal contract class, the registry enforces:

- **Channel uniqueness**: Each channel maps to exactly one processor.
- **Processor availability**: Dispatching a ticket for an unregistered channel raises `LookupError`.
- **Registry immutability at runtime**: Processors cannot be added/removed after runtime initialization.

## WorkItem Contract

All work items must implement `WorkItem` (`src/policy_engine/contracts/work_item.py`).

#### Required Invariants

- **`identifier`**: Must be stable and unique across the system lifetime.
- **`channel`**: Must be immutable and match registered processor channels.
- **`payload`**: Must be a read-only mapping of string keys to string values.

## Runtime Behavior Preservation

All invariants above are designed to preserve runtime behavior:

- Dispatching a ticket always attempts to find a matching processor.
- Missing processors raise `LookupError` (not `KeyError` or `AttributeError`).
- Processing always returns a `RunResult` with deterministic structure.
- Repository operations do not affect processing logic directly.

## Summary

Extensions must conform to:

| Contract | Abstract Class | Key Invariants |
|----------|----------------|----------------|
| Processor | `Processor` | `name`, `supports`, `process` |
| Repository | `WorkItemRepository` | `save`, `get`, `list_by_channel`, `list_all` |
| WorkItem | `WorkItem` | `identifier`, `channel`, `payload` |
| Registry | Runtime-managed | Channel → Processor mapping, immutability |

Violating any invariant may cause runtime errors or undefined behavior.
