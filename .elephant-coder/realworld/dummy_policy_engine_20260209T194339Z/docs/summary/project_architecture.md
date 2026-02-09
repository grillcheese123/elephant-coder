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
- **Processor**: Defines `name`, `supports()`, and `process()` methods. Handles channel-specific work.
- **WorkItemRepository**: Defines `save()`, `get()`, `list_by_channel()`, and `list_all()` methods. Persistence boundary.

## Concrete Subclasses

- **Ticket**: Implements `WorkItem` using `ticket_id`, `target_channel`, and `data`. Immutable via `@dataclass(frozen=True)`.
- **RunResult**: Immutable dataclass capturing processing outcome: `processor`, `item_id`, `success`, `details`.

## Dispatch Flow

1. A `Ticket` is created and persisted via `WorkItemRepository.save()`.
2. A dispatcher retrieves items (e.g., `list_by_channel()`), checks `Processor.supports()`.
3. Matching `Processor.process()` is invoked with the `Ticket`.
4. Result is captured as `RunResult` for audit/tracing.

This design enforces separation of concerns, testability, and extensibility for new channels or persistence layers.