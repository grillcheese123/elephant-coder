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
│   ├── guarded_processor.py
│   └── prioritized_processor.py
└── models/
    └── run_result.py       # RunResult (dataclass)
```

## Abstract Contracts

- **PolicyRule**: `name: str`, `allows(item: WorkItem) -> bool`
- **Processor**: `name: str`, `supports(item: WorkItem) -> bool`, `process(item: WorkItem) -> RunResult`
- **WorkItem**: `identifier: str`, `channel: str`, `payload: dict[str, str]`
- **WorkItemRepository**: `save`, `get`, `list_by_channel`, `list_all`

## Layered Inheritance Chain

1. `GuardedProcessor(BaseProcessor)`
2. `PrioritizedProcessor(GuardedProcessor, AuditableMixin)`

Concrete policies:
- `AllowAllRule(PolicyRule)`
- `RequiredPayloadKeysRule(PolicyRule)`

## Dispatch Flow

1. `PrioritizedProcessor.process(item)`
2. → `GuardedProcessor.process(item)`
3. → `policy.allows(item)` (e.g., `AllowAllRule`, `RequiredPayloadKeysRule`)
4. → `AuditableMixin.build_audit_prefix()` for logging
5. → `RunResult` returned

All contracts and implementations follow strict naming and layered design.