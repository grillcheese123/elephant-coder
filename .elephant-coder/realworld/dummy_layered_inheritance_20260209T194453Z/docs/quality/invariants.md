# Architectural Invariants

This document describes the layered extension contracts and architectural invariants of the layered inheritance engine.

## Overview

The engine enforces a strict layered architecture composed of four core contract families:

1. **Policy Contract** – defines eligibility rules for processing work items
2. **Processor Hierarchy** – defines processing behavior with guard and priority layers
3. **Registry Contract** – coordinates processor discovery and dispatch
4. **Repository Contract** – defines persistence boundaries for work items

These invariants ensure extensibility while preserving runtime behavior and traceability.

---

## 1. Policy Contract

**Contract file**: `src/layered_engine/contracts/policy_rule.py`

The `PolicyRule` abstract base class defines the interface for eligibility evaluation:

```python
class PolicyRule(ABC):
    @property
    @abstractmethod
    def name(self) -> str: ...

    @abstractmethod
    def allows(self, item: WorkItem) -> bool: ...
```

### Invariants

- Every policy must have a stable, unique `name` for auditability.
- The `allows` method must be pure (no side effects) and deterministic.
- Policies are composable: implementations may delegate or combine multiple rules.

### Example Implementations

- `AllowAllRule`: Always returns `True`.
- `RequiredPayloadKeysRule`: Validates presence of required keys in the payload.

---

## 2. Processor Hierarchy

**Core contract**: `src/layered_engine/contracts/processor.py`

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

### Layered Extension

The engine enforces a layered processor hierarchy:

| Layer | Mixin/Class | Purpose |
|-------|-------------|--------|
| Base | `GuardedProcessor` | Wraps a `PolicyRule` to enforce eligibility before processing |
| Audit | `AuditableMixin` | Adds structured audit prefix to results |
| Priority | `PrioritizedProcessor` | Extends `GuardedProcessor` with priority metadata |
| Push | `PushProcessor` | Implements channel-specific delivery logic |

### Invariants

- All processors must implement `supports` to enable dynamic dispatch.
- `process` must return a `RunResult` with `success`, `details`, `processor`, and `item_id`.
- Guarded processors must evaluate policy *before* processing (policy-first invariant).
- Audit metadata must be consistent across all layers.

---

## 3. Registry Contract

**Contract file**: `src/layered_engine/runtime/registry.py`

The registry coordinates processor discovery and dispatch:

```python
def build_default_runtime() -> Runtime:
    # Registers processors by channel (e.g., "email", "push")
    # Returns a runtime with dispatch(item: WorkItem) -> RunResult
```

### Invariants

- Each channel maps to exactly one active processor at runtime.
- Processor registration must be explicit (no auto-discovery).
- Dispatch must fail with a clear `LookupError` if no processor supports the item’s channel.

---

## 4. Repository Contract

**Contract file**: `src/layered_engine/contracts/repository.py`

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

### Invariants

- Persistence operations must be idempotent for `save`.
- `get` must return `None` for missing identifiers (never raise).
- `list_by_channel` must include only items matching the exact channel.
- Repository implementations must preserve `WorkItem.identifier` integrity.

---

## Runtime Behavior Preservation

All invariants are designed to preserve existing runtime behavior:

- Dispatch flow: `registry.dispatch(ticket)` → `processor.supports(item)` → `policy.allows(item)` → `processor.process(item)`.
- Audit trail: Every `RunResult` includes `processor` and `item_id` for traceability.
- Error handling: Missing channel processors raise `LookupError`; policy violations skip processing silently.

---

## Summary

| Contract | Core Invariant |
|----------|----------------|
| Policy | Deterministic, side-effect-free eligibility |
| Processor | Policy-first, channel-specific, auditable |
| Registry | Explicit channel-to-processor mapping |
| Repository | Idempotent, traceable persistence |

These invariants enable safe extension while maintaining correctness and auditability.
