# Architectural Invariants

This document describes the extension contracts and architectural invariants that ensure consistency and extensibility across the Event Mesh engine.

## Extension Points

### 1. Processor Contract

All channel-specific processors must implement the `Processor` abstract base class (`src/event_mesh/contracts/processor.py`):

- **`name`**: Read-only property returning a human-readable identifier.
- **`supports(item: WorkItem) -> bool`**: Determines if the processor can handle the given work item.
- **`process(item: WorkItem) -> RunResult`**: Executes processing logic and returns a result.

**Inheritance Rules**:
- Must inherit from `Processor` (no multiple inheritance).
- All abstract methods must be implemented.
- `supports()` must be deterministic and side-effect-free.

### 2. Repository Contract

All persistence layers must implement `WorkItemRepository` (`src/event_mesh/contracts/repository.py`):

- **`save(item: WorkItem)`**: Persist a work item.
- **`get(identifier: str) -> WorkItem | None`**: Retrieve by ID.
- **`list_by_channel(channel: str) -> list[WorkItem]`**: Filter by channel.
- **`list_all() -> list[WorkItem]`**: Return all items.

**Invariants**:
- `save()` must be idempotent.
- `get()` must return `None` for non-existent IDs.
- `list_by_channel()` and `list_all()` must return fresh copies or immutable views.

### 3. Registry Contract (Implicit)

The `Runtime` (e.g., `build_default_runtime()`) acts as the registry, mapping channels to processors. While not a formal contract, the following invariants apply:

- Each channel maps to exactly one processor.
- Processor registration must occur before `dispatch()` calls.
- Unregistered channels raise `LookupError` during dispatch.

## Work Item Contract

All work items must implement `WorkItem` (`src/event_mesh/contracts/work_item.py`):

- **`identifier: str`**: Unique, immutable ID.
- **`channel: str`**: Target delivery channel.
- **`payload: dict[str, str]`**: Message content.

## Run Result Contract

`RunResult` (`src/event_mesh/models/run_result.py`) is a frozen dataclass with:

- `processor: str`
- `item_id: str`
- `success: bool`
- `details: str`

No custom logic is allowed—pure data carrier.

## Summary

These contracts enforce separation of concerns, testability, and extensibility while preserving runtime behavior across implementations.