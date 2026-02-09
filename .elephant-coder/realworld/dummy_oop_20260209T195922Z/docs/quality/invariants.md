# Architectural Invariants

This document specifies the extension contracts and architectural invariants that must be preserved when extending the workflow engine.

## Registry Contract

The registry is responsible for registering and resolving processor instances by channel.

### Interface

- `register(processor: Processor) -> None`: Register a processor for its supported channel(s).
- `get_processor(channel: str) -> Processor`: Resolve the processor for a given channel.
- `list_registered() -> list[str]`: List all registered channel names.

### Invariants

- Each channel maps to exactly one processor.
- Attempting to register a second processor for an existing channel raises `ValueError`.
- `get_processor(channel)` raises `LookupError` if no processor is registered for the channel.

### Extension Rules

- New processors must implement the `Processor` contract.
- Processors must declare a unique `name` property.
- Processors must implement `supports(item)` to determine applicability.

## Processor Inheritance Rules

Processors implement the `Processor` abstract base class and extend `BaseProcessor` for shared behavior.

### Abstract Contract (`Processor`)

- `name: str`: Human-readable identifier.
- `supports(item: WorkItem) -> bool`: Predicate for item eligibility.
- `process(item: WorkItem) -> RunResult`: Execute processing logic.

### Base Implementation (`BaseProcessor`)

- Implements `supports(item)` to check `item.channel == self.name`.
- Implements `process(item)` to call `_deliver(item)` and wrap in `RunResult`.
- Provides `_deliver(item) -> str`: Abstract delivery method for subclasses.

### Concrete Processors

- `EmailProcessor`, `SmsProcessor`, `PushProcessor`, `WebhookProcessor` extend `BaseProcessor`.
- Each implements `_deliver(item)` with channel-specific delivery logic.
- All must preserve the `supports` and `process` invariants.

### Invariants

- `supports(item)` must be deterministic and idempotent.
- `process(item)` must not mutate the input `WorkItem`.
- `_deliver(item)` must return a stable identifier for the delivered message.

## Repository Contract

The repository abstracts persistence of `WorkItem` instances.

### Interface (`WorkItemRepository`)

- `save(item: WorkItem) -> None`: Persist an item.
- `get(identifier: str) -> WorkItem | None`: Retrieve by ID.
- `list_by_channel(channel: str) -> list[WorkItem]`: Filter by channel.
- `list_all() -> list[WorkItem]`: Retrieve all items.

### Invariants

- `save(item)` must persist `item.identifier`, `item.channel`, and `item.payload` atomically.
- `get(identifier)` must return the same item if previously saved.
- `list_by_channel(channel)` must return only items with matching `item.channel`.
- `list_all()` must return all persisted items.

### Extension Rules

- New repository implementations must preserve all invariants.
- Repository must not mutate stored `WorkItem` instances.
- Repository operations must be thread-safe if used concurrently.

## WorkItem Contract

All work items must satisfy:

- `identifier: str`: Unique, immutable, and stable across runs.
- `channel: str`: Target delivery channel.
- `payload: dict[str, str]`: Message data.

Extensions must not alter these properties or their semantics.