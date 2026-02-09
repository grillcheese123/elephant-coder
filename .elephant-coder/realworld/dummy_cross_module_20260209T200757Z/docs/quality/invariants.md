# Architectural Invariants

This document specifies the extension contracts and architectural invariants that must be preserved when extending the cross-module engine.

## Delivery Interface Contract

The `DeliveryInterface` defines the minimal contract for channel delivery adapters.

```python
from abc import ABC, abstractmethod
from typing import Protocol

class DeliveryInterface(ABC):
    @property
    @abstractmethod
    def channel(self) -> str: ...

    @abstractmethod
    def emit(self, message: str) -> str: ...
```

**Invariants**:
- `channel` must return a non-empty string identifying the target channel.
- `emit` must transform and "send" the message, returning a delivery confirmation string.
- Implementations must be stateless or safely reentrant.

**Extensions must**:
- Implement both `channel` and `emit`.
- Preserve the semantics that `emit` is idempotent for the same message.

## Cross-Module Processor Hierarchy

Processors form a strict hierarchy with clear responsibilities:

1. `Processor` (abstract base)
   - `name: str`
   - `supports(item: WorkItem) -> bool`
   - `process(item: WorkItem) -> RunResult`

2. `ChannelBoundProcessor` (abstract)
   - Binds a `DeliveryInterface` adapter.
   - Provides `render_message(item)` and `_deliver(item)` helpers.

3. `PushProcessor` (concrete)
   - Implements `supports` by matching `item.channel == "push"`.
   - Delegates delivery via `_get_adapter()` and `_render_message()`.

4. `ReliableProcessor` (concrete)
   - Extends `ChannelBoundProcessor`.
   - Overrides `process` to wrap `_deliver` in reliability logic (retry, persistence, etc.).

**Invariants**:
- `supports` must be deterministic and not mutate state.
- `process` must return a `RunResult` with `success`, `processor`, and `details`.
- Subclasses must not override `supports` unless they extend the matching logic.

**Extensions must**:
- Inherit from `Processor` or a known subclass.
- Respect the `supports` → `process` delegation chain.
- Preserve `RunResult` shape and semantics.

## Registry Contract

The `Registry` binds processors to channels at runtime.

```python
class Registry:
    def register(self, processor: Processor) -> None: ...
    def resolve(self, item: WorkItem) -> Processor: ...
```

**Invariants**:
- `resolve(item)` must return exactly one processor if `supports(item)` is true for any registered processor.
- `resolve(item)` must raise `LookupError` if no processor supports the item.
- Registration order must not affect resolution semantics.

**Extensions must**:
- Register processors via `Registry.register` before `build_default_runtime()`.
- Ensure `supports` and `resolve` are consistent.

## Repository Contract

The `WorkItemRepository` abstracts persistence for work items.

```python
class WorkItemRepository(ABC):
    @abstractmethod
    def save(self, item: WorkItem) -> None: ...

    @abstractmethod
    def get(self, identifier: str) -> WorkItem | None: ...

    @abstractmethod
    def list_by_channel(self, channel: str) -> list[WorkItem]: ...

    @abstractmethod
    def list_all(self) -> list[WorkItem] -> list[WorkItem]: ...
```

**Invariants**:
- `save` must persist the item without mutating it.
- `get(identifier)` must return the same item (by identity) if previously saved.
- `list_by_channel` must return only items where `item.channel == channel`.
- `list_all` must return all persisted items.

**Extensions must**:
- Implement all four methods.
- Preserve idempotency of `save` for the same item identifier.
