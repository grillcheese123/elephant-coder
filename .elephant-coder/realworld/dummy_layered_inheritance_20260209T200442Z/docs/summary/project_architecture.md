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

- **PolicyRule**: Evaluates `allows(item: WorkItem) -> bool`; requires `name: str`.
- **Processor**: Handles `process(item: WorkItem) -> RunResult`; requires `name`, `supports`, `process`.
- **WorkItem**: Defines `identifier`, `channel`, `payload`.
- **WorkItemRepository**: Persistence boundary with `save`, `get`, `list_by_channel`, `list_all`.

## Layered Inheritance Chain

1. `GuardedProcessor(BaseProcessor)` → enforces `PolicyRule` check before processing.
2. `PrioritizedProcessor(GuardedProcessor, AuditableMixin)` → adds audit prefix and overrides `process`.

## Dispatch Flow

1. `PrioritizedProcessor.process(item)` is invoked.
2. `AuditableMixin.build_audit_prefix()` prepends context.
3. `GuardedProcessor.process(item)` checks `policy.allows(item)`.
4. If allowed, the underlying processor logic executes; result wrapped in `RunResult`.

All components follow strict ABC contracts and layered composition.