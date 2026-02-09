# Architectural Invariants

This document specifies extension contracts and architectural invariants for the Event Mesh engine.

## Overview

The system enforces strict extension rules to ensure consistency, testability, and maintainability. All extension points are defined via abstract contracts and must adhere to inheritance and behavioral invariants.

---

## Extension Contracts

### 1. Processor Contract (`src/event_mesh/contracts/processor.py`)

All channel-specific processors must:

- **Inherit** from `Processor` (abstract base class).
- **Implement**:
  - `name: str` — human-readable identifier.
  - `supports(item: WorkItem) -> bool` — determines applicability.
  - `process(item: WorkItem) -> RunResult` — executes processing logic.

#### Invariants

- `supports()` must be **deterministic** and **side-effect-free**.
- `process()` must **never mutate** the input `WorkItem`.
- `process()` must return a `RunResult` with accurate `success` flag and `details`.

---

### 2. Repository Contract (`src/event_mesh/contracts/repository.py`)

All persistence implementations must:

- **Inherit** from `WorkItemRepository` (abstract base class).
- **Implement**:
  - `save(item: WorkItem) -> None`
  - `get(identifier: str) -> WorkItem | None`
  - `list_by_channel(channel: str) -> list[WorkItem]`
  - `list_all() -> list[WorkItem]`

#### Invariants

- `save()` must be **idempotent** for the same `WorkItem.identifier`.
- `get()` must return `None` if the item does not exist.
- `list_by_channel()` and `list_all()` must return **consistent snapshots**.

---

### 3. Registry Contract (Implicit)

While no explicit `Registry` class exists, the runtime enforces:

- **Channel-to-Processor Mapping**:
  - Each channel (e.g., `email`, `push`) must have **at most one** registered processor.
  - The runtime uses `Processor.supports()` to select processors.

#### Invariants

- **Uniqueness**: No two processors may claim `supports(item)` for the same `WorkItem`.
- **Completeness**: The runtime must handle all dispatched `WorkItem.channel` values (either via processor or explicit unavailability).

---

## WorkItem Contract (`src/event_mesh/contracts/work_item.py`)

All work items must:

- **Inherit** from `WorkItem` (abstract base class).
- **Implement**:
  - `identifier: str`
  - `channel: str`
  - `payload: dict[str, str]`

#### Invariants

- `identifier` must be **globally unique** and **immutable**.
- `channel` must be **non-empty** and **immutable**.
- `payload` must be **shallow-copied** before mutation by any component.

---

## Summary

| Contract | Abstract Base | Key Invariants |
|---|---|---|
| Processor | `Processor` | Deterministic `supports()`, immutable input, accurate `RunResult` |
| Repository | `WorkItemRepository` | Idempotent `save()`, consistent `list*()` |
| WorkItem | `WorkItem` | Immutable `identifier`, `channel`, `payload` |
| Registry | Runtime-enforced | Unique processor per channel, explicit unavailability handling |

These invariants ensure predictable behavior, simplify testing, and prevent runtime side effects.