# Project Architecture

## File Map

```
src/layered_engine/
├── __init__.py
├── contracts/
│   ├── __init__.py
│   ├── policy_rule.py      # PolicyRule (ABC)
│   ├── processor.py        # Processor (ABC)
│   ├── repository.py       # WorkItemRepository (ABC)
│   └── work_item.py        # WorkItem (ABC)
├── policies/
│   └── basic_rules.py      # AllowAllRule, RequiredPayloadKeysRule
├── processors/
│   ├── auditable_mixin.py  # AuditableMixin
│   ├── guarded_processor.py  # GuardedProcessor
│   └── prioritized_processor.py  # PrioritizedProcessor
└── models/
    ├── __init__.py
    └── run_result.py       # RunResult (dataclass)
```

## Abstract Contracts

- **PolicyRule**: Evaluates if a `WorkItem` passes policy checks (`allows(item) -> bool`).
- **Processor**: Handles `WorkItem`s for a channel (`supports(item)`, `process(item) -> RunResult`).
- **WorkItem**: Immutable unit of work with `identifier`, `channel`, and `payload`.
- **WorkItemRepository**: Persistence boundary (`save`, `get`, `list_by_channel`, `list_all`).

## Layered Inheritance Chain

1. `PolicyRule` (ABC)
   - `AllowAllRule`: Always allows items.
   - `RequiredPayloadKeysRule`: Validates required keys in payload.
2. `Processor` (ABC)
   - `GuardedProcessor`: Wraps a `PolicyRule` and delegates to `process()` only if `policy.allows(item)`.
   - `PrioritizedProcessor`: Extends `GuardedProcessor` with `AuditableMixin` for audit logging.

## Dispatch Flow

1. `PrioritizedProcessor.process(item)` checks `policy.allows(item)`.
2. If allowed, it logs via `AuditableMixin.build_audit_prefix()` and executes processing.
3. Returns `RunResult` with processor name, item ID, success flag, and details.

All contracts are imported via `layered_engine.contracts.__init__`.