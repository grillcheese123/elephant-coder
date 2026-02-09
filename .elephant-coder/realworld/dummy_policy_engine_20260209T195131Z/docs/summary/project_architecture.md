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

- **WorkItem**: Defines `identifier`, `channel`, and `payload` properties. Base unit of work.
- **Processor**: Defines `name`, `supports()`, and `process()` methods. Handles channel-specific logic.
- **WorkItemRepository**: Defines `save()`, `get()`, `list_by_channel()`, and `list_all()`. Persistence boundary.

## Concrete Subclasses

- **Ticket**: Implements `WorkItem` with `ticket_id`, `target_channel`, and `data`. Used as the primary work item type.
- **RunResult**: Immutable dataclass capturing processing outcome: `processor`, `item_id`, `success`, `details`.

## Dispatch Flow

1. A `Ticket` is created and persisted via `WorkItemRepository`.
2. A dispatcher selects a `Processor` that `supports()` the `Ticket`’s channel.
3. The selected `Processor.process()` is invoked with the `Ticket`.
4. A `RunResult` is returned and stored for auditability.

This design enforces separation of concerns, testability, and extensibility for channel-specific processing.