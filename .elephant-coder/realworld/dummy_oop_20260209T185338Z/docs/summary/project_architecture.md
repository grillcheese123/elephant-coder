# Project Architecture

## File-Level Map

```
src/event_mesh/
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

### `WorkItem` (`contracts/work_item.py`)
- **Purpose**: Unit of work dispatched through the system.
- **Abstract properties**:
  - `identifier: str` — stable ID for traceability.
  - `channel: str` — delivery channel (e.g., email, sms).
  - `payload: dict[str, str]` — message content.

### `Processor` (`contracts/processor.py`)
- **Purpose**: Processes work items for a supported channel.
- **Abstract members**:
  - `name: str` — human-readable name.
  - `supports(item: WorkItem) -> bool` — eligibility check.
  - `process(item: WorkItem) -> RunResult` — execution.

### `WorkItemRepository` (`contracts/repository.py`)
- **Purpose**: Persistence boundary for work items.
- **Abstract methods**:
  - `save(item: WorkItem) -> None`
  - `get(identifier: str) -> WorkItem | None`
  - `list_by_channel(channel: str) -> list[WorkItem]`
  - `list_all() -> list[WorkItem]`

## Concrete Subclasses

### `Ticket` (`models/ticket.py`)
- **Implements**: `WorkItem`
- **Fields**:
  - `ticket_id: str` → `identifier`
  - `target_channel: str` → `channel`
  - `data: dict[str, str]` → `payload`
- **Immutable** (`frozen=True`).

### `RunResult` (`models/run_result.py`)
- **Type**: `@dataclass(frozen=True)`
- **Fields**:
  - `processor: str`
  - `item_id: str`
  - `success: bool`
  - `details: str`

## Dispatch Flow

No dispatch logic is implemented yet. The architecture defines:

1. **WorkItem** (`Ticket`) is created with `identifier`, `channel`, and `payload`.
2. A `Processor` subclass would:
   - Check `supports(item)`.
   - Call `process(item)` returning `RunResult`.
3. A `WorkItemRepository` implementation would persist and retrieve items.

Dispatch orchestration (e.g., routing items to processors) is not present in the current codebase.