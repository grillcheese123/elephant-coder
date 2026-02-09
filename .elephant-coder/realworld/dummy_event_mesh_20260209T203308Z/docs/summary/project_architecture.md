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
- **Processor**: Defines `name`, `supports(item)`, and `process(item)` for channel-specific processing.
- **WorkItemRepository**: Defines `save`, `get`, `list_by_channel`, and `list_all` for persistence.

## Concrete Subclasses

- **Ticket**: Implements `WorkItem` with `ticket_id`, `target_channel`, and `data`. Provides concrete property implementations.
- **RunResult**: Immutable dataclass capturing processor execution outcome (`processor`, `item_id`, `success`, `details`).

## Dispatch Flow

1. A `Ticket` is created and persisted via `WorkItemRepository.save`.
2. A dispatcher retrieves items (e.g., via `list_by_channel`) and selects a `Processor` using `supports`.
3. The selected processor executes `process`, returning a `RunResult`.
4. Results are recorded for observability and retry logic.

This design enforces separation of concerns, testability, and extensibility across channels and storage backends.