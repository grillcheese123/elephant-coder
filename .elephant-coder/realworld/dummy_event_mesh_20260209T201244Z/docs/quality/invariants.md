# Architectural Invariants

This document describes the extension contracts and architectural invariants that ensure consistency and extensibility in the Event Mesh engine.

## Extension Contracts

### Processor Contract

All channel processors must implement the `Processor` abstract base class (`src/event_mesh/contracts/processor.py`).

**Required implementation:**
- `name: str` — Human-readable processor name (e.g., `"email"`, `"sms"`).
- `supports(item: WorkItem) -> bool` — Determines whether this processor can handle the given work item.
- `process(item: WorkItem) -> RunResult` — Executes processing logic and returns a result.

**Invariants:**
- `supports()` must be deterministic and side-effect free.
- `process()` must be idempotent for the same `WorkItem`.
- `name` must be unique across all registered processors.

### Repository Contract

All persistence layers must implement the `WorkItemRepository` abstract base class (`src/event_mesh/contracts/repository.py`).

**Required methods:**
- `save(item: WorkItem) -> None`
- `get(identifier: str) -> WorkItem | None`
- `list_by_channel(channel: str) -> list[WorkItem]`
- `list_all() -> list[WorkItem]`

**Invariants:**
- `save()` must persist the item without mutating the input.
- `get()` must return `None` if the item does not exist.
- `list_by_channel()` and `list_all()` must return fresh lists (no shared references).

### Registry Contract

The runtime maintains a registry of processors and repositories. While not yet formalized as an abstract class, the registry enforces:

- **Uniqueness**: Each processor must register with a unique `name`.
- **Fallback handling**: If no processor supports a `WorkItem`, dispatching raises `LookupError`.
- **Extensibility**: New processors and repositories can be added without modifying core runtime logic.

## Architectural Invariants

### Processor Inheritance Rules

- All processors must inherit from `Processor` and implement all abstract methods.
- No concrete processor may override `name`, `supports`, or `process` with non-abstract implementations.
- Processors must not mutate shared state during `supports()` or `process()`.

### Work Item Immutability

- `WorkItem` instances are immutable after creation (via `ABC` properties).
- All properties (`identifier`, `channel`, `payload`) must be stable for the lifetime of the item.

### Run Result Semantics

- `RunResult` is a frozen dataclass: immutable and hashable.
- `success: bool` indicates whether the processing completed without exceptions.
- `details: str` must contain human-readable context (e.g., error messages or success summary).

## Summary

These invariants ensure that:
- The system remains extensible without breaking changes.
- Runtime behavior is deterministic and testable.
- Contract violations are caught early via abstract base classes.
