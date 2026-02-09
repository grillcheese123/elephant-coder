# Architectural Invariants

This document specifies extension contracts and architectural invariants that must be preserved to maintain correctness and extensibility of the Cross Module Engine.

---

## Delivery Interface Contract

**Source:** `src/cross_module_engine/interfaces/delivery_interface.py`

The `DeliveryInterface` defines the minimal contract for channel delivery adapters:

- `channel() -> str`
  - Returns the canonical channel identifier (e.g., `email`, `push`).
- `emit(message: str) -> str`
  - Renders and dispatches a message, returning the final payload string.

**Implementation:** `DeliveryAdapter` in `src/cross_module_engine/channels/delivery_adapter.py`:

- Stores channel and a `MessageTemplate` instance.
- `emit` delegates to `MessageTemplate.render`, which prefixes content with the channel name.

**Invariant:**
- All delivery adapters must be stateless with respect to message content.
- `emit` must be idempotent for the same message and channel.

---

## Cross-Module Processor Hierarchy

**Source:** `src/cross_module_engine/processors/`

Processors implement a consistent interface and are organized hierarchically:

- Base: `ChannelBoundProcessor`
  - Holds a `DeliveryInterface` instance.
  - Provides `channel()` and `emit()` helpers.
- Concrete processors (`PushProcessor`, `ReliableProcessor`, etc.):
  - Implement `process(work_item: WorkItem) -> RunResult`.
  - Must raise `LookupError` if the channel is unsupported.

**Invariant:**
- Processors must not mutate the incoming `WorkItem`.
- `process` must be pure with respect to external state (no side effects beyond `emit`).

---

## Registry Contract

**Source:** `src/cross_module_engine/runtime/registry.py`

The `ProcessorRegistry` is the central dispatcher:

- `get_processor(item: WorkItem) -> Processor`
  - Returns a processor capable of handling `item.channel`.
  - Raises `LookupError` if no processor supports the channel.

**Invariant:**
- The registry must be immutable after initialization.
- `get_processor` must be deterministic and side-effect free.

---

## Repository Contract

**Source:** `src/cross_module_engine/contracts/work_item.py`

The `WorkItem` contract defines the minimal payload for processing:

- `identifier: str`
- `channel: str`
- `payload: dict[str, str]`

**Invariant:**
- `WorkItem` instances must be immutable after construction.
- `payload` must not contain nested structures or binary data.

---

## Extension Guidelines

To extend the engine safely:

1. **Delivery adapters** must implement `DeliveryInterface` and preserve `emit` semantics.
2. **Processors** must subclass `ChannelBoundProcessor` and respect the `process` contract.
3. **Registry** must be updated only via controlled registration hooks (not direct mutation).
4. **WorkItems** must be constructed with valid `identifier`, `channel`, and flat `payload`.

Violating these invariants may cause runtime failures or inconsistent state without altering the current demo behavior.