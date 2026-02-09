# Architectural Invariants

This document describes the extension contracts and architectural invariants of the workflow engine.

## Extension Contracts

### Registry Contract

The registry is responsible for managing available processors and routing work items to appropriate handlers.

**Invariants:**
- Processors must be registered by name before dispatch
- Duplicate processor names are disallowed
- Registry lookup must be deterministic (same name → same processor)
- Unregistered channel requests raise `LookupError`

**Implementation:**
- `src/workflow_engine/runtime/registry.py`
- Uses a dictionary-backed registry with name-based indexing

### Processor Inheritance Rules

Processors implement the `Processor` contract and extend `BaseProcessor` for shared behavior.

**Invariants:**
- All processors must implement `name`, `supports()`, and `process()`
- `supports()` must be idempotent and side-effect-free
- `process()` must not mutate input `WorkItem`
- `BaseProcessor._deliver()` is the single delivery mechanism for subclasses
- Subclasses must override `_deliver()` to implement channel-specific logic

**Contract Hierarchy:**
- `Processor` (abstract base)
  - `BaseProcessor` (concrete base with shared logic)
    - `EmailProcessor`
    - `SmsProcessor`
    - `PushProcessor`
    - `WebhookProcessor`

### Repository Contract

The repository abstracts persistence for work items.

**Invariants:**
- `save()` must persist item without mutation
- `get()` must return identical item on subsequent calls
- `list_by_channel()` must include only items matching the channel
- `list_all()` must return all persisted items
- Repository implementations must be thread-safe for concurrent reads

**Implementation:**
- `src/workflow_engine/contracts/repository.py` (interface)
- `src/workflow_engine/repositories/in_memory_repository.py` (default implementation)

## Work Item Contract

All work items implement the `WorkItem` contract:

- `identifier`: Stable unique ID for traceability
- `channel`: Target delivery channel (e.g., "email", "sms")
- `payload`: Message data as `dict[str, str]`

**Implementation:**
- `src/workflow_engine/contracts/work_item.py` (abstract base)
- `src/workflow_engine/models/ticket.py` (concrete `Ticket` implementation)

## Runtime Behavior

All invariants preserve existing runtime behavior:
- Dispatch flow unchanged
- Error handling (e.g., `LookupError` for unregistered channels) preserved
- Repository persistence semantics unchanged
- Processor inheritance chain maintained