# Architectural Invariants

This document describes extension contracts and architectural invariants that must be preserved across implementations.

## Extension Contracts

### Registry Contract

The runtime registry is responsible for managing processors and repositories. It must:

- Support dynamic registration of `Processor` and `WorkItemRepository` implementations
- Provide lookup by channel for dispatching work items
- Enforce uniqueness of registered components

### Processor Inheritance Rules

All processors must inherit from `Processor` and implement:

- `name: str` — Human-readable identifier for logging and diagnostics
- `supports(item: WorkItem) -> bool` — Deterministic channel and payload compatibility check
- `process(item: WorkItem) -> RunResult` — Side-effect-free processing logic returning a result

Processors must be stateless or safely thread-local to ensure deterministic dispatch behavior.

### Repository Contract

All repositories must implement `WorkItemRepository` with:

- `save(item: WorkItem)` — Persist work items without modifying them
- `get(identifier: str) -> WorkItem | None` — Retrieve by stable identifier
- `list_by_channel(channel: str) -> list[WorkItem]` — Filter items by channel
- `list_all() -> list[WorkItem]` — Return all stored items

Repositories must preserve immutability of `WorkItem` instances.

## Architectural Invariants

- **No runtime behavior changes**: All implementations must preserve the semantics of `run_dispatch_demo.py`
- **Contract-bound extensions**: New processors and repositories must conform to abstract contracts
- **Deterministic dispatch**: `runtime.dispatch()` must raise `LookupError` for unsupported channels
- **Traceability**: All `WorkItem.identifier` values must remain stable across persistence boundaries