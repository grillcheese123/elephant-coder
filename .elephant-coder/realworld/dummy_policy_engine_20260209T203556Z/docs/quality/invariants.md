# Architectural Invariants

This document describes the extension contracts and architectural invariants enforced in the Policy Engine.

## Extension Contracts

### Registry Contract (Planned)

A registry contract is planned to manage available processors. It will:
- Register processors by channel
- Provide lookup by channel or item
- Enforce uniqueness of registered processor names

*Note: This contract is not yet implemented.*

### Processor Contract

All channel processors must inherit from `Processor` (defined in `policy_engine.contracts.processor`).

**Invariants:**
- Must implement `name: str` property (human-readable identifier)
- Must implement `supports(item: WorkItem) -> bool` method
- Must implement `process(item: WorkItem) -> RunResult` method
- Processors must be stateless or safely thread-safe
- `supports()` must be idempotent and deterministic

**Example:**
```python
from policy_engine.contracts.processor import Processor

class EmailProcessor(Processor):
    @property
    def name(self) -> str:
        return "email"

    def supports(self, item: WorkItem) -> bool:
        return item.channel == "email"

    def process(self, item: WorkItem) -> RunResult:
        # Implementation
```

### Repository Contract

All persistence layers must implement `WorkItemRepository` (defined in `policy_engine.contracts.repository`).

**Invariants:**
- `save(item: WorkItem) -> None`: Persist item; must be idempotent
- `get(identifier: str) -> WorkItem | None`: Retrieve by stable ID
- `list_by_channel(channel: str) -> list[WorkItem]`: Filter by channel
- `list_all() -> list[WorkItem]`: Return all stored items
- All methods must be thread-safe or documented as non-thread-safe

## Architectural Invariants

1. **Separation of Concerns:**
   - Contracts define *what* must be done
   - Models define *data structures*
   - Runtime/processors define *how* work is done

2. **Extensibility via Inheritance:**
   - New channels require new `Processor` subclasses
   - New storage backends require new `WorkItemRepository` subclasses

3. **Runtime Behavior Preservation:**
   - Adding new contracts or implementations must not alter existing runtime behavior
   - All abstract methods must be fully implemented before use

4. **Traceability:**
   - `WorkItem.identifier` must be stable and globally unique
   - `RunResult` must include `item_id` and `processor` for audit trails
