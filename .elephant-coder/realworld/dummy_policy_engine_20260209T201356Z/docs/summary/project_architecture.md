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
└── ...
```

## Abstract Contracts

- **WorkItem**: Abstract base for units of work; defines `identifier`, `channel`, and `payload` properties.
- **Processor**: Abstract base for channel-specific processors; defines `name`, `supports()`, and `process()`.
- **WorkItemRepository**: Abstract persistence boundary; defines `save()`, `get()`, `list_by_channel()`, and `list_all()`.

## Concrete Subclasses

- **Ticket**: Concrete implementation of `WorkItem` using `@dataclass(frozen=True)`; fields: `ticket_id`, `target_channel`, `data`.
- **RunResult**: Immutable result model (processor name, item ID, success flag, details).

## Dispatch Flow

1. A `Ticket` is created with an ID, channel, and payload.
2. `WorkItemRepository` persists and retrieves tickets.
3. `Processor.supports()` determines which processor handles a ticket.
4. `Processor.process()` executes and returns a `RunResult`.

This design enforces separation of concerns and supports extensibility via new processor/repository implementations.