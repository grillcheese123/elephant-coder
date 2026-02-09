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
    └── run_result.py       # RunResult (dataclass)
```

## Abstract Contracts

- **PolicyRule**: Evaluates if a `WorkItem` passes policy checks (`allows(item)`) and has a `name`.
- **Processor**: Handles `WorkItem`s with `supports(item)` and `process(item)` returning `RunResult`.
- **WorkItem**: Immutable unit of work with `identifier`, `channel`, and `payload`.
- **WorkItemRepository**: Persistence boundary with `save`, `get`, `list_by_channel`, `list_all`.

## Layered Inheritance Chain

1. `GuardedProcessor(BaseProcessor)`
   - Enforces a `PolicyRule` before processing.
2. `PrioritizedProcessor(GuardedProcessor, AuditableMixin)`
   - Adds audit logging via `AuditableMixin.build_audit_prefix()`.

## Dispatch Flow

1. `PrioritizedProcessor.process(item)` is invoked.
2. `GuardedProcessor.process(item)` checks `policy.allows(item)`.
3. If allowed, `AuditableMixin.build_audit_prefix()` logs context.
4. Concrete processing logic executes and returns `RunResult`.

Policy rules:
- `AllowAllRule`: Always returns `True`.
- `RequiredPayloadKeysRule`: Validates presence of required keys in `WorkItem.payload`.