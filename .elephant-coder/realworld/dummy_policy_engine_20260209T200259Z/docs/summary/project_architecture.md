# Project Architecture

## File Map

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
└── ... (other modules)
```

## Abstract Contracts

- **WorkItem** (`contracts/work_item.py`): Abstract base for units of work. Defines `identifier`, `channel`, and `payload` properties.
- **Processor** (`contracts/processor.py`): Abstract base for channel-specific processors. Defines `name`, `supports()`, and `process()`.
- **WorkItemRepository** (`contracts/repository.py`): Persistence boundary for work items. Defines `save()`, `get()`, `list_by_channel()`, and `list_all()`.

## Concrete Subclasses

- **Ticket** (`models/ticket.py`): Concrete implementation of `WorkItem`. Used as the primary work item type. Fields: `ticket_id`, `target_channel`, `data`.
- **RunResult** (`models/run_result.py`): Immutable result of processing one work item. Fields: `processor`, `item_id`, `success`, `details`.

## Dispatch Flow

1. A `Ticket` is created and persisted via `WorkItemRepository.save()`.
2. A dispatcher retrieves items (e.g., via `list_by_channel(channel)`) and selects a `Processor` whose `supports()` returns `True`.
3. The processor’s `process()` method executes and returns a `RunResult`.
4. Results are stored or reported for observability.

This design enforces separation of concerns, testability, and extensibility for new channels or persistence layers.