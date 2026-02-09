# Architectural Invariants

This document describes the extension contracts and architectural invariants that ensure consistency and correctness across the workflow engine.

## Registry Contract

The registry serves as the central contract for processor discovery and management. It must:

- Support registration of processor instances by channel name
- Provide deterministic lookup of processors by channel
- Raise `LookupError` when no processor is registered for a requested channel
- Maintain immutability of registered processors after initialization

The registry is implemented in `src/workflow_engine/runtime/registry.py` and used by the dispatcher to resolve processors.

## Processor Inheritance Rules

All processors must adhere to the following inheritance and implementation rules:

1. **Base Contract**: All processors implement the `Processor` interface defined in `src/workflow_engine/contracts/processor.py`

2. **Abstract Methods**:
   - `name: str` - Human-readable processor name
   - `supports(item: WorkItem) -> bool` - Determine if the processor can handle the item
   - `process(item: WorkItem) -> RunResult` - Execute processing logic

3. **Inheritance Hierarchy**:
   - `BaseProcessor` (in `src/workflow_engine/processors/base_processor.py`) provides default implementation of `supports()` and `process()`
   - Concrete processors (`EmailProcessor`, `SmsProcessor`, `PushProcessor`, `WebhookProcessor`) extend `BaseProcessor`
   - Concrete processors must implement `_deliver(item: WorkItem) -> str` for channel-specific delivery logic

4. **Extension Guidelines**:
   - New processors must extend `BaseProcessor`
   - New processors must implement `_deliver()` with channel-specific behavior
   - Processor name must match the target channel name for correct routing

## Repository Contract

The repository contract defines the persistence boundary for work items:

1. **Abstract Interface**: Defined in `src/workflow_engine/contracts/repository.py`

2. **Required Methods**:
   - `save(item: WorkItem) -> None` - Persist a work item
   - `get(identifier: str) -> WorkItem | None` - Retrieve by identifier
   - `list_by_channel(channel: str) -> list[WorkItem]` - List items for a channel
   - `list_all() -> list[WorkItem]` - List all stored items

3. **Implementation Requirements**:
   - Repository implementations must be thread-safe for concurrent access
   - `save()` must assign stable identifiers to new items
   - `get()` must return `None` for non-existent identifiers
   - List operations must return fresh copies to prevent external mutation

4. **Current Implementation**: `InMemoryRepository` in `src/workflow_engine/repositories/in_memory_repository.py` provides in-memory storage for testing and development.

## Work Item Contract

Work items are the fundamental units of work in the system:

1. **Abstract Interface**: Defined in `src/workflow_engine/contracts/work_item.py`

2. **Required Properties**:
   - `identifier: str` - Stable identifier for traceability
   - `channel: str` - Target delivery channel
   - `payload: dict[str, str]` - Message payload

3. **Implementation**: `Ticket` in `src/workflow_engine/models/ticket.py` provides concrete implementation with immutable fields.

## Runtime Behavior Preservation

All architectural invariants are designed to preserve existing runtime behavior:

- Processor resolution follows the same dispatch logic
- Repository persistence semantics remain unchanged
- Work item immutability is maintained
- Error handling (e.g., `LookupError` for missing processors) is preserved

Extensions must not alter the observable behavior of existing components.