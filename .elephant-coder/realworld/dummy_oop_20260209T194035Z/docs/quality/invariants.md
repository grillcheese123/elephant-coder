# Architectural Invariants

This document describes the extension contracts and architectural invariants that ensure consistency and maintainability across the workflow engine.

## Registry Contract

The registry is responsible for managing available processors. It must:

- Support registration of processors by name
- Provide lookup of processors by channel
- Raise `LookupError` when no processor supports a given channel

The registry is implemented in `src/workflow_engine/runtime/registry.py` and must be extended when adding new processor types.

## Processor Inheritance Rules

All processors must adhere to the following inheritance hierarchy:

- `Processor` (abstract base class) defines the contract:
  - `name: str` — human-readable identifier
  - `supports(item: WorkItem) -> bool` — determines applicability
  - `process(item: WorkItem) -> RunResult` — executes processing logic

- `BaseProcessor` provides default implementation:
  - Implements `supports()` to check channel match
  - Implements `process()` to delegate to `_deliver()`
  - Defines abstract `_deliver()` for subclasses

- Concrete processors (`EmailProcessor`, `SmsProcessor`, `PushProcessor`, `WebhookProcessor`) extend `BaseProcessor` and implement `_deliver()`.

**Invariant**: No processor may override `supports()` or `process()` directly; extension must occur via `_deliver()`.

## Repository Contract

The repository abstracts persistence for work items:

- `WorkItemRepository` (abstract base class) defines:
  - `save(item: WorkItem) -> None`
  - `get(identifier: str) -> WorkItem | None`
  - `list_by_channel(channel: str) -> list[WorkItem]`
  - `list_all() -> list[WorkItem]`

- Concrete implementations (e.g., `InMemoryRepository`) must preserve:
  - Idempotent `save()`
  - Consistent `get()` and `list_*()` behavior
  - Thread-safety where required

## Extension Guidelines

To add a new processor:

1. Implement `_deliver()` in a subclass of `BaseProcessor`
2. Register it in the registry
3. Ensure channel uniqueness

To add a new repository:

1. Implement all abstract methods in `WorkItemRepository`
2. Preserve contract semantics (e.g., `get()` returns `None` for missing items)
