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

- **WorkItem**: Abstract base for units of work. Defines `identifier`, `channel`, and `payload` properties.
- **Processor**: Abstract base for channel-specific processors. Defines `name`, `supports()`, and `process()` methods.
- **WorkItemRepository**: Abstract persistence boundary. Defines `save()`, `get()`, `list_by_channel()`, and `list_all()` methods.

## Concrete Subclasses

- **Ticket**: Concrete implementation of `WorkItem`. Stores `ticket_id`, `target_channel`, and `data`. Implements required properties.
- **RunResult**: Immutable dataclass capturing processing outcome: `processor`, `item_id`, `success`, and `details`.

## Dispatch Flow

1. A `Ticket` is created with a channel and payload.
2. A `Processor` is selected via `supports()`.
3. The processor’s `process()` method executes and returns a `RunResult`.
4. The result is persisted via `WorkItemRepository.save()`.

This design enforces separation of concerns and supports extensibility via new processor/repository implementations.