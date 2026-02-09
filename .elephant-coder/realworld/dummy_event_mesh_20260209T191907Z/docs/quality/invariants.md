# Architectural Invariants

This document specifies extension contracts and architectural invariants for the Event Mesh engine.

## Extension Contracts

### Registry Contract

The runtime maintains a registry of processors to enable dynamic dispatch. The registry must:

- Support registration of processors by name
- Allow lookup of processors by supported channel
- Return `None` when no processor is registered for a given channel

### Processor Inheritance Rules

All processors must inherit from `event_mesh.contracts.processor.Processor` and implement:

- `name: str` — Human-readable identifier for logging and diagnostics
- `supports(item: WorkItem) -> bool` — Predicate determining if the processor can handle the item
- `process(item: WorkItem) -> RunResult` — Execution logic returning a result object

Processors must be stateless or safely thread-local to support concurrent dispatch.

### Repository Contract

All repositories must inherit from `event_mesh.contracts.repository.WorkItemRepository` and implement:

- `save(item: WorkItem) -> None` — Persist an item
- `get(identifier: str) -> WorkItem | None` — Retrieve by ID
- `list_by_channel(channel: str) -> list[WorkItem]` — Filter by target channel
- `list_all() -> list[WorkItem]` — Full scan support

Repositories must ensure idempotent `save` operations to support retry semantics.

## Architectural Invariants

- **Runtime behavior must remain unchanged** — All invariants are design-time guarantees; no behavioral changes are introduced.
- **Contracts are abstract** — All contracts use `abc.ABC` and `@abstractmethod` to enforce implementation at compile time.
- **No circular dependencies** — Contracts depend only on models and other contracts, never on concrete implementations.
- **Result immutability** — `RunResult` is a frozen dataclass to prevent side effects after dispatch.
