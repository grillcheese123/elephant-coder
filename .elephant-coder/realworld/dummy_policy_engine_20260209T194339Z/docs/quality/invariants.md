# Architectural Invariants

This document describes extension contracts and architectural invariants that must be preserved to maintain system correctness.

## Extension Points

### Registry Contract

The registry is responsible for managing processors by channel. It must:

- Support registration of `Processor` instances by channel name
- Provide lookup of processors for a given channel
- Ensure only one processor per channel (single-writer invariant)
- Fail fast if duplicate registration is attempted

### Processor Inheritance Rules

All channel processors must inherit from `policy_engine.contracts.processor.Processor` and implement:

- `name: str` — human-readable identifier
- `supports(item: WorkItem) -> bool` — predicate for eligibility
- `process(item: WorkItem) -> RunResult` — core execution logic

**Invariants:**

- `supports()` must be deterministic and side-effect free
- `process()` must be idempotent with respect to external side effects (e.g., retries must not duplicate external actions)
- `RunResult.processor` must match the processor’s `name`

### Repository Contract

All repositories must implement `policy_engine.contracts.repository.WorkItemRepository`:

- `save(item: WorkItem) -> None`
- `get(identifier: str) -> WorkItem | None`
- `list_by_channel(channel: str) -> list[WorkItem]`
- `list_all() -> list[WorkItem]`

**Invariants:**

- `save()` must persist the item such that subsequent `get()` or `list_*()` calls reflect the change
- `get()` must return `None` if the item does not exist (never raise on missing keys)
- `list_by_channel()` and `list_all()` must return fresh copies or immutable views to prevent external mutation

## Runtime Behavior

These invariants preserve runtime semantics:

- Dispatching a `Ticket` to a channel always resolves to at most one processor
- Work items are persisted before processing (durability invariant)
- Result objects are immutable (`frozen=True`) to prevent accidental mutation

## Future Extensions

- Additional processor channels must follow the same contract
- Repository implementations may vary (in-memory, DB, etc.) but must uphold the above invariants