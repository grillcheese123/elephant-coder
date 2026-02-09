# Project Architecture

## File Map

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

- **WorkItem**: Defines `identifier`, `channel`, and `payload` properties. Represents a unit of work.
- **Processor**: Defines `name`, `supports()`, and `process()` methods. Handles work items per channel.
- **WorkItemRepository**: Defines `save()`, `get()`, `list_by_channel()`, and `list_all()`. Persistence boundary.

## Concrete Subclasses

- **Ticket**: Implements `WorkItem` with `ticket_id`, `target_channel`, and `data`. Used as the primary work item type.
- **RunResult**: Immutable dataclass capturing processor execution outcome (`processor`, `item_id`, `success`, `details`).

## Dispatch Flow

1. A `Ticket` is created and persisted via `WorkItemRepository.save()`.
2. A dispatcher retrieves items (e.g., via `list_by_channel()`).
3. For each item, `Processor.supports()` selects the appropriate processor.
4. The processor’s `process()` method executes and returns a `RunResult`.
5. Results are stored or logged for observability.