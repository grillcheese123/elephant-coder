# Project Architecture

## File Map
- `src/layered_engine/contracts/`: Abstract interfaces (`PolicyRule`, `Processor`, `WorkItem`, `WorkItemRepository`)
- `src/layered_engine/policies/`: Concrete policy implementations (`AllowAllRule`, `RequiredPayloadKeysRule`)
- `src/layered_engine/processors/`: Processing logic (`GuardedProcessor`, `PrioritizedProcessor`, `AuditableMixin`)
- `src/layered_engine/models/`: Data models (`RunResult`)
- `tests/`: Unit tests (e.g., `test_layering.py`)

## Abstract Contracts
- `PolicyRule`: Abstract base for access control (`name`, `allows`)
- `Processor`: Abstract base for channel processors (`name`, `supports`, `process`)
- `WorkItem`: Abstract unit of work (`identifier`, `channel`, `payload`)
- `WorkItemRepository`: Abstract persistence boundary (`save`, `get`, `list_by_channel`, `list_all`)

## Layered Inheritance Chain
1. `PolicyRule` (ABC)
   - `AllowAllRule`
   - `RequiredPayloadKeysRule`
2. `Processor` (ABC)
   - `GuardedProcessor` (uses `PolicyRule`)
     - `PrioritizedProcessor` (extends `GuardedProcessor`, `AuditableMixin`)

## Dispatch Flow
1. `PrioritizedProcessor.process(item)` is invoked
2. Delegates to `GuardedProcessor.process(item)`
3. `GuardedProcessor` checks `policy.allows(item)`
4. If allowed, processing proceeds; audit logging via `AuditableMixin` is applied
5. Result returned as `RunResult`