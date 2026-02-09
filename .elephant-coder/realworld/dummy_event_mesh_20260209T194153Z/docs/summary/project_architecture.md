# Event Mesh Engine — Project Architecture

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

- **WorkItem**: Defines `identifier`, `channel`, and `payload` properties. Base unit of work.
- **Processor**: Defines `name`, `supports(item)`, and `process(item)` for channel-specific handling.
- **WorkItemRepository**: Defines `save`, `get`, `list_by_channel`, and `list_all` for persistence.

## Concrete Subclasses

- **Ticket**: Implements `WorkItem` with `ticket_id`, `target_channel`, and `data`. Immutable (`frozen=True`).
- **RunResult**: Immutable dataclass capturing processor outcome (`processor`, `item_id`, `success`, `details`).

## Dispatch Flow

1. A `Ticket` is created and persisted via `WorkItemRepository.save`.
2. A dispatcher retrieves items (e.g., via `list_by_channel(channel)`).
3. For each item, `Processor.supports(item)` identifies the appropriate processor.
4. The processor’s `process(item)` executes and returns a `RunResult`.
5. Results are stored or logged for observability.

This design enforces separation of concerns, testability, and extensibility for new channels or persistence layers.