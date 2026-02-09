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
- **Processor**: Defines `name`, `supports()`, and `process()` methods.
- **WorkItemRepository**: Defines `save()`, `get()`, `list_by_channel()`, and `list_all()` methods.

## Concrete Subclasses

- **Ticket**: Implements `WorkItem` with `ticket_id`, `target_channel`, and `data` fields.
- **RunResult**: Immutable dataclass capturing processor execution outcome.

## Dispatch Flow

1. A `Ticket` is created with a channel and payload.
2. A `Processor` checks `supports()` to determine eligibility.
3. The processor calls `process()` and returns a `RunResult`.
4. The `WorkItemRepository` persists and retrieves items as needed.