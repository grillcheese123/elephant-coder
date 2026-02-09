# Project Architecture

## File Map

```
src/workflow_engine/
├── __init__.py
├── contracts/
│   ├── __init__.py
│   ├── processor.py          # Processor (ABC)
│   ├── repository.py         # WorkItemRepository (ABC)
│   └── work_item.py          # WorkItem (ABC)
├── models/
│   ├── __init__.py
│   ├── run_result.py         # RunResult (concrete)
│   └── ticket.py             # Ticket (WorkItem concrete)
├── processors/
│   ├── base_processor.py     # BaseProcessor (Processor impl)
│   ├── email_processor.py    # EmailProcessor
│   ├── sms_processor.py      # SmsProcessor
│   └── webhook_processor.py  # WebhookProcessor
├── repositories/
│   └── in_memory_repository.py  # InMemoryWorkItemRepository
├── runtime/
│   ├── bootstrap.py          # Entry point
│   └── registry.py           # Processor registry
├── services/
│   ├── dispatcher.py         # Dispatch logic
│   └── reporting.py          # Reporting service
└── tests/
    └── test_dispatcher.py
```

## Abstract Contracts

- **WorkItem**: Defines `identifier`, `channel`, `payload` — unit of work.
- **Processor**: Defines `name`, `supports()`, `process()` — handles work items by channel.
- **WorkItemRepository**: Defines `save()`, `get()`, `list_by_channel()`, `list_all()` — persistence boundary.

## Concrete Subclasses

- **WorkItem**: `Ticket` (immutable data class).
- **Processor**: `BaseProcessor` (abstract base), `EmailProcessor`, `SmsProcessor`, `WebhookProcessor` (implement `_deliver()`).
- **Repository**: `InMemoryWorkItemRepository` (in-memory dict-backed).

## Dispatch Flow

1. `bootstrap.py` initializes `InMemoryWorkItemRepository`.
2. `registry.py` registers `EmailProcessor`, `SmsProcessor`, `WebhookProcessor`.
3. `dispatcher.py` selects processor via `supports()`, invokes `process()`, persists `RunResult` via repository.
4. `reporting.py` queries repository for analytics.

All components depend only on contracts, enabling testability and extensibility.