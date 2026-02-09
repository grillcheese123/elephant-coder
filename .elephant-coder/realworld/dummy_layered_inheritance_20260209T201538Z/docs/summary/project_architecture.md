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
│   ├── guarded_processor.py # GuardedProcessor
│   └── prioritized_processor.py # PrioritizedProcessor
└── models/
    ├── __init__.py
    └── run_result.py       # RunResult (dataclass)
```

## Abstract Contracts

- **WorkItem**: Abstract unit of work with `identifier`, `channel`, `payload`.
- **PolicyRule**: Abstract policy evaluator with `name` and `allows(item)`.
- **Processor**: Abstract processor with `name`, `supports(item)`, `process(item)`.
- **WorkItemRepository**: Abstract persistence boundary with `save`, `get`, `list_by_channel`, `list_all`.

## Layered Inheritance Chain

1. `GuardedProcessor(BaseProcessor)`
   - Enforces a `PolicyRule` before processing.
2. `PrioritizedProcessor(GuardedProcessor, AuditableMixin)`
   - Adds audit logging via `AuditableMixin`.

## Dispatch Flow

1. `PrioritizedProcessor.process(item)` is invoked.
2. `GuardedProcessor.process(item)` checks `policy.allows(item)`.
3. If allowed, `AuditableMixin.build_audit_prefix()` logs context.
4. Concrete processor logic executes and returns `RunResult`.

## Policy Rules

- **AllowAllRule**: Always returns `True` for `allows()`.
- **RequiredPayloadKeysRule**: Validates presence of required keys in `item.payload`.