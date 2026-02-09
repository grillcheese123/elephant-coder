# Architectural Invariants

This document describes the layered extension contracts and architectural invariants that define the structure and behavior of the layered inheritance engine.

## Overview

The engine enforces a strict layered architecture composed of four core contract families:

1. **Policy Contract** (`PolicyRule`) — authorization and filtering rules
2. **Processor Hierarchy** (`Processor`) — channel-specific processing logic
3. **Registry Contract** (`RuntimeRegistry`) — runtime composition and discovery
4. **Repository Contract** (`WorkItemRepository`) — persistence boundary

All implementations must preserve these invariants to ensure correct dispatch and auditability.

---

## 1. Policy Contract (`PolicyRule`)

**Location**: `src/layered_engine/contracts/policy_rule.py`

### Invariants

- **Deterministic evaluation**: `allows(item)` must be pure and idempotent.
- **Stable identity**: `name` property must be immutable and unique per rule type.
- **No side effects**: Rule evaluation must not mutate the `WorkItem` or external state.

### Contract

```python
class PolicyRule(ABC):
    @property
    @abstractmethod
    def name(self) -> str: ...

    @abstractmethod
    def allows(self, item: WorkItem) -> bool: ...
```

### Implementations

- `AllowAllRule`: Always returns `True` for `allows`.
- `RequiredPayloadKeysRule`: Validates presence of configured keys in `item.payload`.

---

## 2. Processor Hierarchy (`Processor`)

**Location**: `src/layered_engine/contracts/processor.py`

### Invariants

- **Channel affinity**: `supports(item)` must be consistent with the processor’s designated channel.
- **Idempotent dispatch**: Repeated calls with the same item must produce identical `RunResult` metadata.
- **Audit prefix**: Processors using `AuditableMixin` must produce deterministic audit prefixes.

### Contract

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

### Hierarchy

- `AuditableMixin`: Provides `build_audit_prefix()` for structured logging.
- `GuardedProcessor`: Wraps a delegate and enforces a `PolicyRule` before dispatch.
- `PrioritizedProcessor`: Orders processing based on priority metadata.
- `PushProcessor`: Handles push-channel work items.

---

## 3. Registry Contract (`RuntimeRegistry`)

**Location**: `src/layered_engine/runtime/registry.py`

### Invariants

- **Singleton runtime**: `build_default_runtime()` must return a consistent, fully-wired instance.
- **Processor ordering**: `runtime.processors` must be ordered by specificity (e.g., guarded before raw).
- **Repository binding**: The registry must bind a single `WorkItemRepository` instance to all processors.

### Contract

```python
def build_default_runtime() -> Runtime:
    """Constructs a fully-wired runtime with default policy, processor, and repository bindings."""
```

---

## 4. Repository Contract (`WorkItemRepository`)

**Location**: `src/layered_engine/contracts/repository.py`

### Invariants

- **Persistence boundary**: All `save`, `get`, `list_by_channel`, and `list_all` operations must be atomic.
- **Identifier uniqueness**: `get(identifier)` must return at most one item per ID.
- **Channel consistency**: `list_by_channel(channel)` must return only items whose `channel` attribute matches.

### Contract

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

---

## Runtime Behavior Preservation

All invariants are designed to preserve existing runtime behavior:

- Dispatch logic in `run_dispatch_demo.py` remains unchanged.
- No modifications to `WorkItem`, `RunResult`, or `AuditableMixin` implementations.
- All contract methods are strictly typed and abstract, preventing accidental deviation.

---

## References

- `src/layered_engine/contracts/policy_rule.py`
- `src/layered_engine/contracts/processor.py`
- `src/layered_engine/contracts/repository.py`
- `src/layered_engine/runtime/registry.py`
- `src/layered_engine/processors/auditable_mixin.py`
