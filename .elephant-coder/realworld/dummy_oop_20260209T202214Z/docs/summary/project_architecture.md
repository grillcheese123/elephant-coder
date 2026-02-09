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
│   └── ticket.py         # Ticket (WorkItem)
├── processors/
│   ├── base_processor.py      # BaseProcessor (Processor)
│   ├── email_processor.py     # EmailProcessor
│   ├── sms_processor.py       # SmsProcessor
│   └── webhook_processor.py   # WebhookProcessor
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

- **WorkItem**: Abstract unit of work with `identifier`, `channel`, and `payload` properties.
- **Processor**: Abstract processor with `name`, `supports(item)`, and `process(item)` methods.
- **WorkItemRepository**: Abstract persistence boundary with `save`, `get`, `list_by_channel`, and `list_all` methods.

## Concrete Subclasses

- **WorkItem**: `Ticket`
- **Processor**: `BaseProcessor` (abstract base), `EmailProcessor`, `SmsProcessor`, `WebhookProcessor`
- **Repository**: `InMemoryWorkItemRepository`
- **RunResult**: Concrete result model

## Dispatch Flow

1. `bootstrap.py` initializes `InMemoryWorkItemRepository`.
2. `registry.py` registers `EmailProcessor`, `SmsProcessor`, and `WebhookProcessor`.
3. `dispatcher.py` selects a processor via `supports(item)`, calls `process(item)`, and uses `_deliver` to persist results via the repository.
4. `reporting.py` reads from the repository for analytics.

All processors inherit from `BaseProcessor`, which implements `process` and delegates `_deliver` to channel-specific logic.