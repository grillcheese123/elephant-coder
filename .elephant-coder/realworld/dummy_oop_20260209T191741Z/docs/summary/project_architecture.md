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
│   ├── base_processor.py # BaseProcessor (Processor)
│   ├── email_processor.py
│   ├── sms_processor.py
│   └── webhook_processor.py
├── repositories/
│   └── in_memory_repository.py
├── runtime/
│   ├── bootstrap.py
│   └── registry.py
└── services/
    ├── dispatcher.py
    └── reporting.py
```

## Abstract Contracts

- **WorkItem**: Defines `identifier`, `channel`, and `payload` properties.
- **Processor**: Defines `name`, `supports(item)`, and `process(item)` methods.
- **WorkItemRepository**: Defines `save`, `get`, `list_by_channel`, and `list_all` methods.

## Concrete Subclasses

- **WorkItem**: `Ticket`
- **Processor**: `BaseProcessor` (abstract base), `EmailProcessor`, `SmsProcessor`, `WebhookProcessor`
- **WorkItemRepository**: `InMemoryWorkItemRepository`
- **RunResult**: Concrete model for processing outcomes

## Dispatch Flow

1. `bootstrap.py` initializes `InMemoryWorkItemRepository`.
2. `registry.py` registers all processors (`EmailProcessor`, `SmsProcessor`, `WebhookProcessor`).
3. `dispatcher.py` selects a processor via `supports()`, invokes `process()`, and persists results via repository.
4. `reporting.py` queries the repository for analytics.

All processors extend `BaseProcessor`, which implements `process()` and delegates `_deliver()` to channel-specific logic.