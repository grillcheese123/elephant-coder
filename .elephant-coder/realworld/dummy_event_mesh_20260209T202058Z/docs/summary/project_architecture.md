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

- **WorkItem**: Defines `identifier`, `channel`, and `payload` properties.
- **Processor**: Defines `name`, `supports(item)`, and `process(item)`.
- **WorkItemRepository**: Defines `save`, `get`, `list_by_channel`, and `list_all`.

## Concrete Subclasses

- **Ticket**: Implements `WorkItem` with `ticket_id`, `target_channel`, and `data`.
- **RunResult**: Immutable dataclass capturing processor outcome (`processor`, `item_id`, `success`, `details`).

## Dispatch Flow

1. A `Ticket` is created with channel and payload.
2. `WorkItemRepository` persists and retrieves tickets.
3. `Processor.supports()` selects appropriate processor.
4. `Processor.process()` executes and returns `RunResult`.
5. Results are stored for observability and retry logic.