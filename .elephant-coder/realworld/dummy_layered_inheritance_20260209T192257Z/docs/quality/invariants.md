# Architectural Invariants

## Overview

The layered engine enforces a strict contract-based architecture to ensure safe, extensible, and testable processing of work items. This document describes the core contracts and invariants that must be preserved across all extensions.

---

## 1. Policy Contract (`PolicyRule`)

**Contract file**: `src/layered_engine/contracts/policy_rule.py`

### Invariants
- Every policy must implement `name: str` (immutable identifier).
- Every policy must implement `allows(item: WorkItem) -> bool` (deterministic evaluation).
- Policies are stateless unless explicitly designed otherwise (e.g., `RequiredPayloadKeysRule`).
- Policy evaluation must be side-effect free.

### Extension Rules
- New policies must subclass `PolicyRule` and implement both abstract members.
- Do not mutate `WorkItem` inside `allows()`.

---

## 2. Processor Hierarchy

### Base Contract (`Processor`)
**Contract file**: `src/layered_engine/contracts/processor.py`

**Invariants**:
- `name: str` uniquely identifies the processor.
- `supports(item: WorkItem) -> bool` must be deterministic and side-effect free.
- `process(item: WorkItem) -> RunResult` must always return a `RunResult`.

### GuardedProcessor
**File**: `src/layered_engine/processors/guarded_processor.py`

**Invariants**:
- Wraps a `PolicyRule` instance.
- `process()` first evaluates `policy.allows(item)`; if `False`, returns a failure `RunResult`.
- Subclasses must implement `deliver(item: WorkItem) -> RunResult` (core logic).

### PrioritizedProcessor
**File**: `src/layered_engine/processors/prioritized_processor.py`

**Invariants**:
- Extends `GuardedProcessor` and `AuditableMixin`.
- Audit prefix is built via `build_audit_prefix()` before processing.
- `process()` logs audit info before delegating to `deliver()`.

### PushProcessor
**File**: `src/layered_engine/processors/push_processor.py`

**Invariants**:
- Extends `GuardedProcessor` and `AuditableMixin`.
- Uses `RequiredPayloadKeysRule` by default (configurable).
- `supports()` checks `item.channel == "push"`.
- `deliver()` returns success/failure based on payload validation.

### Extension Rules
- All processors must subclass `Processor` (directly or via `GuardedProcessor`).
- Do not override `process()` unless absolutely necessary (prefer `deliver()`).
- Audit and policy guards must not be bypassed.

---

## 3. Registry Contract (`get_processors`)

**File**: `src/layered_engine/runtime/registry.py`

**Invariants**:
- Returns a list of `Processor` instances.
- Order reflects priority (higher priority first).
- No side effects during registration (pure factory function).

### Extension Rules
- New processors must be added to `get_processors()` to be discoverable.
- Do not mutate returned list.

---

## 4. Repository Contract (`WorkItemRepository`)

**Contract file**: `src/layered_engine/contracts/repository.py`

**Invariants**:
- `save(item)` must persist without side effects on the item.
- `get(identifier)` must return `None` if not found.
- `list_by_channel(channel)` and `list_all()` must return fresh lists.
- Repository must not mutate `WorkItem` instances.

### Extension Rules
- Implementations must preserve immutability semantics.
- Do not leak internal state (e.g., avoid returning internal lists).

---

## Runtime Behavior Preservation

All invariants above are designed to ensure:
- Deterministic dispatch via `runtime.dispatch(ticket)`.
- Audit trails are always populated in `RunResult`.
- Policy failures are exposed in `RunResult.details`.
- No changes to runtime behavior are introduced by new extensions.

---

## Summary

| Layer | Contract | Key Invariant |
|-------|----------|---------------|
| Policy | `PolicyRule` | Deterministic, side-effect free `allows()` |
| Processor | `Processor` | `supports()` + `process()` contract |
| Registry | `get_processors()` | Pure, ordered factory |
| Repository | `WorkItemRepository` | Immutable persistence boundary |

Extensions violating these invariants risk breaking dispatch, audit, or policy enforcement.