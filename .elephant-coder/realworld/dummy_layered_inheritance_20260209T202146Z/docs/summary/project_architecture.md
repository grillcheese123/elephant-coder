# Project Architecture

## File Map

```
src/layered_engine/
├── __init__.py
├── contracts/
│   ├── __init__.py
│   ├── policy_rule.py
│   ├── processor.py
│   ├── repository.py
│   └── work_item.py
├── policies/
│   └── basic_rules.py
├── processors/
│   ├── auditable_mixin.py
│   ├── guarded_processor.py
│   └── prioritized_processor.py
└── models/
    ├── __init__.py
    └── run_result.py
```

## Abstract Contracts

- **PolicyRule**: Abstract base for policy evaluation (`allows(item)`, `name`).
- **Processor**: Abstract base for processing work items (`process(item)`, `supports(item)`, `name`).
- **WorkItem**: Abstract base for units of work (`identifier`, `channel`, `payload`).
- **WorkItemRepository**: Abstract persistence boundary (`save`, `get`, `list_by_channel`, `list_all`).

## Layered Inheritance Chain

1. `PolicyRule` (ABC)
   - `AllowAllRule`
   - `RequiredPayloadKeysRule`
2. `Processor` (ABC)
   - `GuardedProcessor`: Wraps a `PolicyRule` to guard `process()`.
   - `PrioritizedProcessor`: Extends `GuardedProcessor` with `AuditableMixin`.
3. `AuditableMixin`: Adds audit prefix generation.

## Dispatch Flow

1. `PrioritizedProcessor.process(item)` is invoked.
2. It delegates to `GuardedProcessor.process(item)`, which:
   - Checks `policy.allows(item)`.
   - If allowed, invokes its own processing logic.
3. Audit logging is applied via `AuditableMixin.build_audit_prefix()`.
4. Result is returned as `RunResult`.

All contracts are defined in `contracts/`, concrete policies in `policies/`, and processors in `processors/`. The system enforces layered composition and clear separation of concerns.