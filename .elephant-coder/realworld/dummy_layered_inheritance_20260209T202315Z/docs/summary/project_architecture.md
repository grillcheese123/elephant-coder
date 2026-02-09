# Project Architecture

## File Map
- `src/layered_engine/contracts/`: Abstract interfaces
- `src/layered_engine/policies/`: Concrete policy implementations
- `src/layered_engine/processors/`: Processing logic with mixins
- `src/layered_engine/models/`: Domain data models

## Abstract Contracts
- `PolicyRule`: Abstract base for access policies (`name`, `allows`)
- `Processor`: Abstract base for channel processors (`name`, `supports`, `process`)
- `WorkItem`: Abstract unit of work (`identifier`, `channel`, `payload`)
- `WorkItemRepository`: Persistence boundary (`save`, `get`, `list_by_channel`, `list_all`)

## Layered Inheritance Chain
1. `PolicyRule` (ABC)
   - `AllowAllRule`: Always allows items
   - `RequiredPayloadKeysRule`: Validates required keys in payload
2. `Processor` (ABC)
   - `GuardedProcessor`: Wraps a `PolicyRule` to guard processing
     - `PrioritizedProcessor`: Extends `GuardedProcessor` with `AuditableMixin` for audit logging

## Dispatch Flow
1. `PrioritizedProcessor.process(item)` checks `policy.allows(item)`
2. If allowed, executes processing and returns `RunResult`
3. Audit prefix built via `AuditableMixin.build_audit_prefix()`
4. Policies evaluated before processing; repository used for persistence

All components follow strict ABC patterns and layered inheritance.