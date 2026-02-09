# Project Architecture

## File Map

```
src/workflow_engine/
├── __init__.py
├── contracts/
│   ├── __init__.py
│   ├── processor.py      # Processor (ABC)
│   ├── repository.py     # WorkItemRepository (ABC)
│   └── work_item.py      # WorkItem (ABC)
├── models/
│   ├── __init__.py
│   ├── run_result.py     # RunResult (concrete)
│   └── ticket.py         # Ticket (WorkItem concrete)
├── processors/
│   ├── base_processor.py     # BaseProcessor (Processor)
│   ├── email_processor.py    # EmailProcessor
│   ├── sms_processor.py      # SmsProcessor
│   └── webhook_processor.py  # WebhookProcessor
├── repositories/
│   └── in_memory_repository.py  # InMemoryWorkItemRepository
├── runtime/
│   ├── bootstrap.py
│   └── registry.py
├── services/
│   ├── dispatcher.py
│   └── reporting.py
└── tests/
    └── test_dispatcher.py
```

## Abstract Contracts

- **WorkItem**: Abstract base for work units with `identifier`, `channel`, `payload` properties.
- **Processor**: Abstract base for channel-specific processing with `name`, `supports()`, `process()`.
- **WorkItemRepository**: Abstract persistence boundary with `save()`, `get()`, `list_by_channel()`, `list_all()`.

## Concrete Subclasses

- **WorkItem**: `Ticket` implements identifier, channel, payload.
- **Processor**: `BaseProcessor` implements core logic; `EmailProcessor`, `SmsProcessor`, `WebhookProcessor` override `_deliver()`.
- **Repository**: `InMemoryWorkItemRepository` provides in-memory storage.

## Dispatch Flow

1. `Dispatcher` selects a `Processor` via `supports()`.
2. `Processor.process()` executes and persists `RunResult` via `Repository.save()`.
3. `BaseProcessor._deliver()` delegates to channel-specific delivery.
4. `Registry` registers all processors; `Bootstrap` initializes runtime.

