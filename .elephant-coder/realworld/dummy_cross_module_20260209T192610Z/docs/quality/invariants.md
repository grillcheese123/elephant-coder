# Architectural Invariants

This document specifies the extension contracts and architectural invariants that must be preserved across the cross-module engine.

## Delivery Interface Contract

The `DeliveryInterface` defines the contract for channel delivery adapters.

**Contract:**
- `channel: str` — read-only property identifying the delivery channel.
- `emit(message: str) -> str` — transforms and returns the rendered message.

**Implementation requirement:**
- All delivery adapters must inherit from `DeliveryInterface` (via `ABC`).
- `emit()` must return a channel-prefixed string (e.g., `"email:..."`).

**Example:**
```python
class DeliveryInterface(ABC):
    @property
    @abstractmethod
    def channel(self) -> str: ...

    @abstractmethod
    def emit(self, message: str) -> str: ...
```

---

## Cross-Module Processor Hierarchy

Processors form a strict inheritance hierarchy with well-defined responsibilities.

**Contract:**
- `Processor` (abstract base) defines `name`, `supports(item)`, and `process(item)`.
- `ChannelBoundProcessor` extends `Processor` and provides:
  - `adapter: DeliveryInterface` — the channel delivery mechanism.
  - `render_message(item)` — renders the work item payload.
  - `_deliver(item)` — invokes `adapter.emit()` on the rendered message.
- Concrete processors (`PushProcessor`, `ReliableProcessor`) implement `process()` by calling `_deliver()`.

**Invariants:**
- `ChannelBoundProcessor` is abstract and must not be instantiated directly.
- `ReliableProcessor` extends `PushProcessor` and preserves its delivery semantics.
- `supports()` must be deterministic and based on item channel.

---

## Registry Contract

The `RuntimeRegistry` serves as the central composition root.

**Contract:**
- `processors: list[Processor]` — ordered list of available processors.
- `repository: WorkItemRepository` — persistence boundary for work items.
- `build_default_runtime()` — constructs a fully wired runtime instance.

**Invariants:**
- Processors are registered in a fixed order (e.g., `ReliableProcessor`, `PushProcessor`).
- The registry must be immutable after construction.
- `build_default_runtime()` must produce a consistent, fully-configured runtime.

---

## Repository Contract

The `WorkItemRepository` abstracts persistence for work items.

**Contract:**
- `save(item)` — persist a work item.
- `get(identifier)` — fetch one item by ID, or `None`.
- `list_by_channel(channel)` — list items for a specific channel.
- `list_all()` — list all stored items.

**Invariants:**
- `get()` must return `None` for missing IDs (no exceptions).
- `list_by_channel()` must return an empty list if no items match.
- Repository implementations must be thread-safe or stateless.

---

## Extension Guidelines

- **New channels:** Implement `DeliveryInterface`, then subclass `ChannelBoundProcessor`.
- **New processors:** Extend `ChannelBoundProcessor`, implement `name` and `process()`.
- **New repositories:** Implement `WorkItemRepository` and wire via `build_default_runtime()`.
- **Breaking changes:** Any change violating these contracts must be documented and tested.
