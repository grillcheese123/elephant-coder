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

- **WorkItem**: Defines `identifier`, `channel`, and `payload` properties. Base unit of work.
- **Processor**: Defines `name`, `supports()`, and `process()` methods. Handles work items per channel.
- **WorkItemRepository**: Defines `save()`, `get()`, `list_by_channel()`, and `list_all()` methods. Persistence boundary.

## Concrete Subclasses

- **Ticket**: Implements `WorkItem` with `ticket_id`, `target_channel`, and `data`. Immutable via `@dataclass(frozen=True)`.
- **RunResult**: Immutable result dataclass with `processor`, `item_id`, `success`, and `details`.

## Dispatch Flow

1. A `Ticket` is created and persisted via `WorkItemRepository.save()`.
2. `WorkItemRepository.list_by_channel(channel)` retrieves items for a channel.
3. A dispatcher selects a `Processor` whose `supports()` returns `True` for the item.
4. The processor’s `process()` method executes and returns a `RunResult`.
5. Results are recorded for observability and retry logic.

All contracts use `@abstractmethod` and `ABC` to enforce implementation contracts. The design supports extensibility for new channels and persistence backends.