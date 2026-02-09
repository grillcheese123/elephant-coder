# Architectural Invariants

This document describes the extension contracts and architectural invariants that ensure consistency and extensibility in the Event Mesh engine.

## Overview

The system enforces strict contracts for core components to guarantee predictable behavior and safe extension. These invariants are enforced at the type and interface level.

## Extension Contracts

### 1. Processor Contract (`src/event_mesh/contracts/processor.py`)

All processors must implement the `Processor` abstract base class:

- **`name`**: Read-only property returning a human-readable identifier.
- **`supports(item: WorkItem) -> bool`**: Determines whether the processor can handle a given work item.
- **`process(item: WorkItem) -> RunResult`**: Executes processing logic and returns a result.

**Inheritance Rules**:
- Processors must inherit from `Processor` (via `class MyProcessor(Processor)`).
- All abstract methods and properties must be implemented.
- No additional required constructor arguments beyond those defined in `__init__`.

### 2. Repository Contract (`src/event_mesh/contracts/repository.py`)

All repositories must implement the `WorkItemRepository` abstract base class:

- **`save(item: WorkItem) -> None`**: Persists a work item.
- **`get(identifier: str) -> WorkItem | None`**: Retrieves a work item by ID.
- **`list_by_channel(channel: str) -> list[WorkItem]`**: Lists items targeting a specific channel.
- **`list_all() -> list[WorkItem]`**: Lists all stored items.

**Inheritance Rules**:
- Repositories must inherit from `WorkItemRepository`.
- All abstract methods must be implemented.
- No side effects beyond persistence (e.g., no network calls in `get`).

### 3. Registry Contract (Implied)

While no explicit registry contract exists yet, the `Runtime` class (`src/event_mesh/runtime.py`) acts as a registry:

- Accepts a list of `Processor` instances during initialization.
- Uses `Processor.supports()` to select appropriate processors.
- Enforces that each dispatched item is processed by exactly one processor.

**Invariants**:
- Processors must be non-overlapping in `supports()` logic to avoid ambiguity.
- The runtime does not mutate processor state during dispatch.

## Architectural Invariants

1. **Work Item Immutability**: `WorkItem.identifier`, `WorkItem.channel`, and `WorkItem.payload` are read-only after construction.
2. **Run Result Immutability**: `RunResult` is a frozen dataclass; results cannot be modified after creation.
3. **No Side Effects in Contracts**: Abstract methods must not assume or cause side effects beyond their documented behavior.
4. **Channel-Based Routing**: Processors must use `item.channel` (via `WorkItem.channel`) to determine support.

## Runtime Behavior Preservation

All invariants are enforced at the type level and do not alter runtime behavior:
- Dispatch logic remains unchanged.
- Repository implementations (e.g., `InMemoryRepository`) continue to function as before.
- No new dependencies or configuration changes required.

## Future Extensions

To add a new processor:
1. Subclass `Processor`.
2. Implement `name`, `supports()`, and `process()`.
3. Register it with `Runtime` via `build_default_runtime()` or custom runtime construction.

To add a new repository:
1. Subclass `WorkItemRepository`.
2. Implement all abstract methods.
3. Inject it into `Runtime` during construction.