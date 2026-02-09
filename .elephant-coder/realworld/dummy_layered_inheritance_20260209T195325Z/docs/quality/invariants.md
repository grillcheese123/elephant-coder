# Architectural Invariants

This document describes the layered extension contracts and architectural invariants that define the structure and behavior of the layered inheritance engine.

## Overview

The engine enforces a strict layered architecture composed of four core contract families:

1. **Policy Contract** (`PolicyRule`) — authorization and filtering
2. **Processor Hierarchy** (`Processor`, `GuardedProcessor`, `PrioritizedProcessor`, `PushProcessor`) — execution logic
3. **Registry Contract** (`Registry`) — processor discovery and dispatch
4. **Repository Contract** (`WorkItemRepository`) — persistence boundary

All invariants are enforced at the contract level; implementations must adhere to the defined interfaces to be compatible with the runtime.

---

## 1. Policy Contract (`PolicyRule`)

**Location**: `src/layered_engine/contracts/policy_rule.py`

### Interface

```python
class PolicyRule(ABC):
    @property
    @abstractmethod
    def name(self) -> str: ...

    @abstractmethod
    def allows(self, item: WorkItem) -> bool: ...
```

### Invariants

- **Deterministic**: `allows(item)` must return the same result for identical `item` instances.
- **Non-mutating**: `allows` must not modify the `WorkItem` or any external state.
- **Idempotent**: Repeated calls with the same input must yield identical results.
- **Fail-safe**: If policy evaluation fails, it must return `False` (deny by default).

### Implementations

- `AllowAllRule`: Always returns `True`.
- `RequiredPayloadKeysRule`: Checks that `item.payload` contains all required keys.

---

## 2. Processor Hierarchy

**Location**: `src/layered_engine/processors/`

### Base Contract (`Processor`)

```python
class Processor(ABC):
    @property
    @abstractmethod
    def name(self) -> str: ...

    @abstractmethod
    def supports(self, item: WorkItem) -> bool: ...

    @abstractmethod
    def process(self, item: WorkItem) -> RunResult: ...
```

### Invariants

- **Channel affinity**: `supports(item)` must be consistent with `item.channel`.
- **Non-blocking**: `process` must not block indefinitely; timeouts must be enforced.
- **Result completeness**: `RunResult` must include `success`, `details`, and optional `audit`.

### Layered Extensions

| Layer | Contract | Invariants |
|-------|----------|------------|
| `GuardedProcessor` | `Processor + PolicyRule` | Must evaluate `policy.allows(item)` before processing; deny if policy fails. |
| `PrioritizedProcessor` | `GuardedProcessor + AuditableMixin` | Must prepend audit prefix via `build_audit_prefix()`; priority ordering enforced. |
| `PushProcessor` | `AuditableMixin + GuardedProcessor` | Must implement `deliver(item)`; `process` delegates to `deliver`. |

### Inheritance Chain

```
Processor
  └── GuardedProcessor (adds policy enforcement)
        └── PrioritizedProcessor (adds audit prefix + priority)
        └── PushProcessor (adds delivery logic + audit)
```

---

## 3. Registry Contract (`Registry`)

**Location**: `src/layered_engine/runtime/registry.py`

### Interface

- `register(processor: Processor) -> None`
- `get_processor(channel: str) -> Processor | None`
- `dispatch(item: WorkItem) -> RunResult`

### Invariants

- **Uniqueness**: Only one processor per `channel` may be registered.
- **Fallback**: If no processor supports an item, `dispatch` must return a failure `RunResult`.
- **Atomic dispatch**: `dispatch` must not partially process items; either full success or full failure.

---

## 4. Repository Contract (`WorkItemRepository`)

**Location**: `src/layered_engine/contracts/repository.py`

### Interface

```python
class WorkItemRepository(ABC):
    @abstractmethod
    def save(self, item: WorkItem) -> None: ...

    @abstractmethod
    def get(self, identifier: str) -> WorkItem | None: ...

    @abstractmethod
    def list_by_channel(self, channel: str) -> list[WorkItem]: ...

    @abstractmethod
    def list_all(self) -> list[WorkItem]: ...
```

### Invariants

- **Persistence isolation**: Repository must not depend on in-memory state outside its scope.
- **Consistency**: `get(identifier)` must return the last-saved state for that ID.
- **Channel filtering**: `list_by_channel` must return only items matching the channel.
- **Non-destructive**: `save` must not overwrite unrelated items.

---

## Runtime Behavior Preservation

All invariants are enforced at compile-time via abstract base classes. Runtime behavior remains unchanged:

- `run_dispatch_demo.py` continues to dispatch `email` and `push` tickets.
- `LookupError` for missing processors (e.g., push) is preserved.
- Audit trails are appended via `AuditableMixin` without altering result semantics.

---

## Summary

| Layer | Contract | Key Invariant |
|-------|----------|---------------|
| Policy | `PolicyRule` | Deny-by-default, deterministic evaluation |
| Processor | `Processor` → `GuardedProcessor` → `PrioritizedProcessor`/`PushProcessor` | Policy guard before processing |
| Registry | `Registry` | One processor per channel, atomic dispatch |
| Repository | `WorkItemRepository` | Persistent, consistent, channel-scoped storage |

These invariants ensure extensibility while preserving correctness and traceability across all layers.