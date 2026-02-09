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

- **WorkItem**: Abstract base for units of work; defines `identifier`, `channel`, and `payload` properties.
- **Processor**: Abstract base for channel-specific processors; defines `name`, `supports()`, and `process()`.
- **WorkItemRepository**: Persistence boundary; defines `save()`, `get()`, `list_by_channel()`, and `list_all()`.

## Concrete Subclasses

- **Ticket**: Concrete `WorkItem` implementation with `ticket_id`, `target_channel`, and `data` fields.
- **RunResult**: Immutable dataclass capturing processor outcome (`processor`, `item_id`, `success`, `details`).

## Dispatch Flow

1. A `Ticket` is created and persisted via `WorkItemRepository.save()`.
2. A dispatcher retrieves items (e.g., via `list_by_channel()`).
3. For each item, it selects a `Processor` via `supports()`.
4. The processor executes `process()` and returns a `RunResult`.
5. Results are stored or reported for auditing.

This design enforces separation of concerns and supports extensibility via new `Processor` and `WorkItem` implementations.