# Architectural Invariants

This document describes the layered extension contracts and architectural invariants of the layered inheritance engine.

## Overview

The engine enforces a strict layered architecture composed of four core contract families:

1. **Policy Contract** (`PolicyRule`) — authorization and filtering
2. **Processor Hierarchy** — execution and dispatch
3. **Registry Contract** — processor discovery and registration
4. **Repository Contract** — persistence boundary

All invariants are enforced via abstract base classes and concrete implementations must adhere to their contracts to ensure runtime correctness.

---

## 1. Policy Contract (`PolicyRule`)

**File**: `src/layered_engine/contracts/policy_rule.py`

```python
class PolicyRule(ABC):
    @property
    @abstractmethod
    def name(self) -> str: ...

    @abstractmethod
    def allows(self, item: WorkItem) -> bool: ...
```

### Invariants

- Every policy must have a stable, unique `name` for identification.
- `allows(item)` must be deterministic and side-effect free.
- Policies are composable: implementations may chain or combine other policies.

### Known Implementations

- `AllowAllRule`: Always returns `True`.
- `RequiredPayloadKeysRule`: Validates presence of required keys in `WorkItem.payload`.

---

## 2. Processor Hierarchy

**Base Contract**: `Processor` (`src/layered_engine/contracts/processor.py`)

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

### Layered Extensions

#### `GuardedProcessor`

- Wraps a `PolicyRule` instance.
- Enforces policy check before processing.
- Invariant: `process(item)` calls `policy.allows(item)` first; if `False`, returns failure.

#### `AuditableMixin`

- Adds audit trail capability via `build_audit_prefix()`.
- Invariant: Audit prefix includes processor name and timestamp.

#### `PrioritizedProcessor`

- Extends `GuardedProcessor` + `AuditableMixin`.
- Invariant: Processes items in priority order (if priority metadata present).

#### `PushProcessor`

- Extends `GuardedProcessor` + `AuditableMixin`.
- Implements channel-specific delivery via `deliver(item)`.
- Invariant: `supports(item)` checks `item.channel == "push"`.

---

## 3. Registry Contract (`Registry`)

**File**: `src/layered_engine/runtime/registry.py`

```python
class Registry(ABC):
    @abstractmethod
    def register(self, processor: Processor) -> None: ...

    @abstractmethod
    def find_processor(self, channel: str) -> Processor | None: ...

    @abstractmethod
    def list_processors(self) -> list[Processor]: ...
```

### Invariants

- Processor registration is idempotent: re-registering same `name` has no effect.
- `find_processor(channel)` returns the first processor whose `supports(item)` returns `True` for any `item` with that channel.
- Registry must be thread-safe for concurrent reads.

---

## 4. Repository Contract (`WorkItemRepository`)

**File**: `src/layered_engine/contracts/repository.py`

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

- `save(item)` must persist `item.identifier` uniquely.
- `get(identifier)` must return the same `WorkItem` (by value) on subsequent calls.
- `list_by_channel` and `list_all` must return consistent snapshots.

---

## Runtime Behavior Preservation

All invariants are enforced at the contract level; concrete implementations must not alter runtime semantics beyond what is defined by their contracts. The `run_dispatch_demo.py` script demonstrates correct usage without side effects.

---

## Summary Table

| Contract          | File(s)                                      | Key Invariant                                  |
|-------------------|----------------------------------------------|------------------------------------------------|
| `PolicyRule`      | `contracts/policy_rule.py`                   | Deterministic, side-effect-free `allows()`     |
| `Processor`       | `contracts/processor.py`                     | `supports()` + `process()` must be consistent |
| `Registry`        | `runtime/registry.py`                        | Idempotent registration, channel lookup       |
| `WorkItemRepository` | `contracts/repository.py`                | Persistent, idempotent `save()` and `get()`   |
