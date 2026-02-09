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
└── ... (other modules)
```

## Abstract Contracts

- **WorkItem**: Defines `identifier`, `channel`, and `payload` properties. Represents a unit of work.
- **Processor**: Defines `name`, `supports()`, and `process()` methods. Handles work items for specific channels.
- **WorkItemRepository**: Defines `save()`, `get()`, `list_by_channel()`, and `list_all()` methods. Abstracts persistence.

## Concrete Subclasses

- **Ticket**: Implements `WorkItem` using `ticket_id`, `target_channel`, and `data`. Immutable via `@dataclass(frozen=True)`.
- **RunResult**: Immutable dataclass capturing processor execution outcome (`processor`, `item_id`, `success`, `details`).

## Dispatch Flow

1. A `Ticket` is created with an identifier, channel, and payload.
2. A `Processor` implementation checks `supports()` to determine eligibility.
3. If supported, `process()` executes and returns a `RunResult`.
4. `WorkItemRepository` implementations persist and retrieve `Ticket` instances.

This design enforces separation of concerns, testability, and extensibility via interface-based contracts.