# Architectural Invariants

This document specifies the extension contracts and architectural invariants that must be preserved across the cross-module engine.

---

## Delivery Interface Contract

**Location:** `src/cross_module_engine/interfaces/delivery_interface.py`

The `DeliveryInterface` defines the minimal contract for channel delivery adapters:

- `channel: str` — read-only property identifying the delivery channel.
- `emit(message: str) -> str` — transforms and dispatches a message, returning the final payload.

Implementations:
- `DeliveryAdapter` — concrete adapter that uses a `MessageTemplate` to format messages.

Invariants:
- All adapters must be immutable with respect to channel identity.
- `emit` must be pure (no side effects) and deterministic for the same input.

---

## Cross-Module Processor Hierarchy

**Location:** `src/cross_module_engine/processors/`

### Base Contract

- `Processor` (abstract) — defines `name`, `supports`, and `process` methods.

### Channel-Bound Base

- `ChannelBoundProcessor` extends `Processor` and adds:
  - `adapter: DeliveryInterface` — lazily resolved delivery adapter.
  - `render_message(item: WorkItem) -> str` — formats the message using the adapter.
  - `_deliver(item: WorkItem) -> str` — invokes `adapter.emit` and returns the result.

### Concrete Processors

- `PushProcessor` — handles `push` channel items.
- `ReliableProcessor` — wraps delivery in reliability semantics (e.g., retries).

Invariants:
- All processors must be stateless except for the adapter reference.
- `supports` must be deterministic and based solely on `WorkItem.channel`.
- `process` must delegate to `_deliver` and wrap the result in a `RunResult`.

---

## Registry Contract

**Location:** `src/cross_module_engine/runtime/registry.py`

The registry is responsible for routing work items to the correct processor:

- `register(processor: Processor)` — adds a processor by name.
- `get_processor(channel: str) -> Processor` — resolves the processor for a channel.
- `process(item: WorkItem) -> RunResult` — dispatches an item to the appropriate processor.

Invariants:
- The registry must be immutable after initialization.
- `process` must raise `LookupError` if no processor supports the item’s channel.
- All registered processors must be mutually exclusive in `supports` (no ambiguous matches).

---

## Repository Contract

**Location:** `src/cross_module_engine/contracts/repository.py`

The `WorkItemRepository` defines the persistence boundary:

- `save(item: WorkItem) -> None`
- `get(identifier: str) -> WorkItem | None`
- `list_by_channel(channel: str) -> list[WorkItem]`
- `list_all() -> list[WorkItem]`

Invariants:
- Repository operations must be idempotent for `save` and `get`.
- `list_by_channel` must return only items matching the exact channel.
- No repository implementation is required for runtime; it is an extension point.

---

## Extension Guidelines

- New channels require a new `Processor` subclass and a corresponding `DeliveryInterface` implementation.
- The registry must be updated to register new processors.
- All contracts must remain stable to preserve runtime behavior.
