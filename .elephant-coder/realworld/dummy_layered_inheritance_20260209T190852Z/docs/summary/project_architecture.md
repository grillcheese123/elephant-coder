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
├── models/
│   ├── __init__.py
│   └── run_result.py       # RunResult (dataclass)
├── policies/
│   └── basic_rules.py      # AllowAllRule, RequiredPayloadKeysRule
└── processors/
    ├── auditable_mixin.py  # AuditableMixin
    ├── guarded_processor.py  # GuardedProcessor
    └── prioritized_processor.py  # PrioritizedProcessor
```

## Abstract Contracts

- **PolicyRule**: Evaluates `allows(item: WorkItem) -> bool`; defines `name` property.
- **Processor**: Defines `name`, `supports(item)`, and `process(item) -> RunResult`.
- **WorkItem**: Abstract unit with `identifier`, `channel`, and `payload`.
- **WorkItemRepository**: Persistence boundary with `save`, `get`, `list_by_channel`, `list_all`.

## Layered Inheritance Chain

1. `GuardedProcessor(BaseProcessor)`
   - Enforces a `PolicyRule` before processing.
   - Delegates to `process(item)` only if `policy.allows(item)`.
2. `PrioritizedProcessor(GuardedProcessor, AuditableMixin)`
   - Adds audit logging via `AuditableMixin.build_audit_prefix()`.
   - Implements `process(item)` with policy guard and audit prefix.

## Dispatch Flow

1. `WorkItem` enters system.
2. `PrioritizedProcessor.process(item)` checks policy via `GuardedProcessor.policy.allows(item)`.
3. If allowed, audit prefix is prepended, then processing proceeds.
4. Result returned as `RunResult` with processor name, item ID, success flag, and details.

