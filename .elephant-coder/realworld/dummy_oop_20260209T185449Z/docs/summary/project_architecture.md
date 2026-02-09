# Project Architecture

## File-Level Map

```
src/policy_engine/
├── __init__.py
├── contracts/
│   ├── __init__.py
│   ├── processor.py      # Processor (ABC)
│   ├── repository.py     # WorkItemRepository (ABC)
│   └── work_item.py      # WorkItem (ABC)
├── models/
│   ├── __init__.py
│   ├── run_result.py     # RunResult (dataclass)
│   └── ticket.py         # Ticket (concrete WorkItem)
└── ...
```

## Abstract Contracts

### WorkItem (src/policy_engine/contracts/work_item.py)
- **Purpose**: Unit of work dispatched through the system.
- **Abstract properties**:
  - `identifier: str` — stable ID for traceability.
  - `channel: str` — delivery channel (e.g., email, sms).
  - `payload: dict[str, str]` — message payload.

### Processor (src/policy_engine/contracts/processor.py)
- **Purpose**: Processes work items for a supported channel.
- **Abstract members**:
  - `name: str` — human-readable name.
  - `supports(item: WorkItem) -> bool` — eligibility check.
  - `process(item: WorkItem) -> RunResult` — execution.

### WorkItemRepository (src/policy_engine/contracts/repository.py)
- **Purpose**: Persistence boundary for work items.
- **Abstract methods**:
  - `save(item: WorkItem) -> None`
  - `get(identifier: str) -> WorkItem | None`
  - `list_by_channel(channel: str) -> list[WorkItem]`
  - `list_all() -> list[WorkItem]`

## Concrete Subclasses

### Ticket (src/policy_engine/models/ticket.py)
- **Implements**: WorkItem
- **Fields**:
  - `ticket_id: str`
  - `target_channel: str`
  - `data: dict[str, str]`
- **Properties**:
  - `identifier` → `ticket_id`
  - `channel` → `target_channel`
  - `payload` → `data`

### RunResult (src/policy_engine/models/run_result.py)
- **Type**: Immutable dataclass (frozen=True)
- **Fields**:
  - `processor: str`
  - `item_id: str`
  - `success: bool`
  - `details: str`

## Dispatch Flow

1. A `Ticket` is created with `ticket_id`, `target_channel`, and `data`.
2. A `Processor` implementation (not yet present) would:
   - Check `supports(ticket)`.
   - Call `process(ticket)`.
   - Return a `RunResult`.
3. The `WorkItemRepository` (not yet implemented) would persist the `Ticket` and `RunResult`.

No dispatch logic is implemented yet; only contracts and domain models exist.