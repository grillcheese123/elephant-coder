# Architectural Invariants

This document specifies extension contracts and architectural invariants for the workflow engine.

## Extension Points

### Registry Contract

The registry is responsible for mapping channels to processors. It must support:

- **Registration**: Register a processor instance for a specific channel.
- **Lookup**: Retrieve the processor responsible for a given channel.
- **Exhaustive Coverage**: Every dispatched work item must have a registered processor for its target channel.

Violating this invariant (e.g., dispatching to an unregistered channel) results in a `LookupError`.

### Processor Inheritance Rules

All processors must adhere to the following inheritance hierarchy:

- `Processor` (abstract contract)
  - `BaseProcessor` (concrete base implementation)
    - `EmailProcessor`
    - `SmsProcessor`
    - `PushProcessor`
    - `WebhookProcessor`

Each concrete processor must:

1. Extend `BaseProcessor` (do not implement `Processor` directly).
2. Implement `_deliver(item: WorkItem) -> str` with channel-specific delivery logic.
3. Implement `name` property returning a human-readable identifier.
4. Implement `supports(item: WorkItem) -> bool` to check channel compatibility.
5. Implement `process(item: WorkItem) -> RunResult` to orchestrate delivery and persistence.

### Repository Contract

The repository abstracts persistence of work items. Implementations must satisfy:

- `save(item: WorkItem) -> None`: Persist an item.
- `get(identifier: str) -> WorkItem | None`: Retrieve by ID.
- `list_by_channel(channel: str) -> list[WorkItem]`: Query by target channel.
- `list_all() -> list[WorkItem]`: Enumerate all stored items.

The in-memory repository (`InMemoryRepository`) is the default implementation.

## Invariant Summary

| Invariant | Requirement | Consequence of Violation |
|-----------|-------------|--------------------------|
| Registry Coverage | Every dispatched channel must have a registered processor | `LookupError` on dispatch |
| Processor Inheritance | All processors must extend `BaseProcessor` | Breaks `supports()` and `process()` semantics |
| Repository Completeness | All work items must be persistable via `save()` | Data loss on dispatch |

These invariants ensure deterministic dispatch behavior and extensibility without modifying core runtime logic.
